from __future__ import annotations
import hashlib, hmac, json, logging, os, socket, uuid, time
from copy import deepcopy
from pathlib import Path
from urllib.parse import urlparse
from ipaddress import ip_address
from typing import Any
import httpx
from fastapi import FastAPI, UploadFile, File, Form, Header, Request, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.errors import EngineError
from app.media import probe_video, sha256_file, VIDEO_EXTS
from app.models import SessionCreate, InstructionRequest, RestoreRequest, RenderRequest
from app.timeline import new_timeline, duration, timeline_hash, clone, export_otio
from app.engine import EditingEngine
from app.render import render_timeline
from app.storage import upload_output
from app.transcription import get_provider, TranscriptionUnavailable

logging.basicConfig(level=logging.INFO,format="%(message)s")
logger=logging.getLogger("incuedit")
app=FastAPI(title="IncuEdit API",version="1.0.0",description="Prompt-based, reversible video editing engine")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)
app.mount("/static",StaticFiles(directory=Path(__file__).resolve().parent.parent/"web"),name="static")
_frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if _frontend_dist.exists():
    app.mount("/app", StaticFiles(directory=_frontend_dist, html=True), name="react_app")

VIDEOS: dict[str,dict]={}
SESSIONS: dict[str,dict]={}
JOBS: dict[str,dict]={}
IDEMPOTENCY: dict[str,dict]={}
engine=EditingEngine()

class RequestContextMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        corr = str(uuid.uuid4())
        headers = scope.get("headers", [])
        for k, v in headers:
            if k.lower() == b"x-correlation-id":
                corr = v.decode("latin1", errors="ignore")
                break
        scope.setdefault("state", {})["correlation_id"] = corr

        method = scope.get("method", "")
        path = scope.get("path", "")
        if method == "POST" and path.startswith("/api/v1/"):
            has_idem = any(k.lower() == b"idempotency-key" for k, _ in headers)
            if not has_idem:
                body = json.dumps({"error":{"code":"IDEMPOTENCY_KEY_REQUIRED","message":"Every POST request must include an Idempotency-Key header.","retryable":False,"details":{}}}).encode("utf-8")
                await send({
                    "type": "http.response.start",
                    "status": 400,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"content-length", str(len(body)).encode("ascii")),
                        (b"x-correlation-id", corr.encode("latin1")),
                    ]
                })
                await send({"type": "http.response.body", "body": body})
                return

        started = time.perf_counter()
        status_holder = {"status": 200}

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_holder["status"] = message.get("status", 200)
                resp_headers = list(message.get("headers", []))
                resp_headers.append((b"x-correlation-id", corr.encode("latin1")))
                message["headers"] = resp_headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            elapsed = (time.perf_counter() - started) * 1000
            logger.info(json.dumps({
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "level": "INFO",
                "job_id": None,
                "correlation_id": corr,
                "method": method,
                "path": path,
                "status_code": status_holder["status"],
                "latency_ms": round(elapsed, 2)
            }))

app.add_middleware(RequestContextMiddleware)

@app.exception_handler(EngineError)
async def engine_error_handler(request: Request, exc: EngineError):
    status=422 if exc.code not in {"RENDER_FAILED","RENDER_TIMEOUT","PROBE_TIMEOUT"} else 500
    return JSONResponse(status_code=status,content={"error":{"code":exc.code,"message":exc.message,"retryable":exc.retryable,"details":exc.details}})

@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException):
    detail=exc.detail if isinstance(exc.detail,dict) else {"message":str(exc.detail)}
    code=detail.get("code","HTTP_ERROR")
    return JSONResponse(status_code=exc.status_code,content={"error":{"code":code,"message":detail.get("message",str(exc.detail)),"retryable":False,"details":detail}})

def _idem(request: Request, payload: Any) -> tuple[str,str|None]:
    key=request.headers.get("Idempotency-Key")
    if not key: raise EngineError("IDEMPOTENCY_KEY_REQUIRED","Idempotency-Key is required.")
    digest=hashlib.sha256(json.dumps(payload,sort_keys=True,default=str).encode()).hexdigest()
    return key,digest

def _check_idem(key: str, digest: str):
    cached=IDEMPOTENCY.get(key)
    if cached:
        if cached["digest"]!=digest: raise EngineError("IDEMPOTENCY_CONFLICT","This Idempotency-Key was already used with a different request.")
        return cached["response"]
    return None

def _store_idem(key: str,digest: str,response: dict):
    IDEMPOTENCY[key]={"digest":digest,"response":response}

def _video_record(path: Path, filename: str, rights_confirmed: bool) -> dict:
    if path.suffix.lower() not in VIDEO_EXTS:
        raise EngineError("UNSUPPORTED_VIDEO_FORMAT","Only MP4 and MOV video files are supported.",details={"extension":path.suffix})
    meta=probe_video(path)
    vid=str(uuid.uuid4())
    record={"video_id":vid,"filename":filename,"path":str(path.resolve()),**meta,"source_sha256":sha256_file(path),"rights_confirmed":rights_confirmed}
    VIDEOS[vid]=record
    return record

@app.get("/", response_class=HTMLResponse)
async def home():
    html_path = Path(__file__).resolve().parent.parent / "web" / "index.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))

@app.get("/health")
@app.get("/api/v1/health")
async def health(): return {"status":"ok","service":"incuedit"}

@app.get("/ready")
@app.get("/api/v1/ready")
async def ready():
    return {"status":"ready","ffmpeg":True,"storage":settings.data_dir.exists()}

@app.post("/api/v1/videos/upload")
async def upload_video(request: Request, file: UploadFile=File(...), rights_confirmed: bool=Form(False)):
    key,digest=_idem(request,{"filename":file.filename,"size":file.size,"rights_confirmed":rights_confirmed})
    cached=_check_idem(key,digest)
    if cached: return cached
    if not rights_confirmed:
        raise EngineError("RIGHTS_CONFIRMATION_REQUIRED","Confirm that you own the video or have permission to use it, and that it may be processed for this assessment.")
    ext=Path(file.filename or "video.mp4").suffix.lower()
    if ext not in VIDEO_EXTS: raise EngineError("UNSUPPORTED_VIDEO_FORMAT","Only MP4 and MOV video files are supported.")
    data=await file.read(settings.max_upload_mb*1024*1024+1)
    if len(data)>settings.max_upload_mb*1024*1024: raise EngineError("UPLOAD_TOO_LARGE",f"Maximum upload size is {settings.max_upload_mb} MB.")
    path=settings.data_dir/"videos"/f"{uuid.uuid4()}{ext}"
    path.write_bytes(data)
    try: record=_video_record(path,file.filename or path.name,rights_confirmed)
    except Exception:
        path.unlink(missing_ok=True); raise
    response={"video":record,"message":"Video uploaded and inspected. Add a transcript to create a session."}
    _store_idem(key,digest,response)
    return response

@app.post("/api/v1/videos/from-url")
async def upload_from_url(request: Request, url: str=Form(...), rights_confirmed: bool=Form(False)):
    key,digest=_idem(request,{"url":url,"rights_confirmed":rights_confirmed})
    cached=_check_idem(key,digest)
    if cached:return cached
    if not rights_confirmed: raise EngineError("RIGHTS_CONFIRMATION_REQUIRED","Confirm that you own the video or have permission to use it.")
    parsed=urlparse(url)
    if parsed.scheme!="https" or not parsed.hostname: raise EngineError("UNSAFE_URL","Only public HTTPS video URLs are accepted.")
    try:
        addresses=socket.getaddrinfo(parsed.hostname,443,type=socket.SOCK_STREAM)
        if not addresses or any(ip_address(x[4][0]).is_private or ip_address(x[4][0]).is_loopback or ip_address(x[4][0]).is_link_local for x in addresses):
            raise EngineError("UNSAFE_URL","Private and local network URLs are not accepted.")
    except EngineError: raise
    except Exception: raise EngineError("URL_DNS_FAILED","The video host could not be resolved.")
    ext=Path(parsed.path).suffix.lower()
    if ext not in VIDEO_EXTS: raise EngineError("UNSUPPORTED_VIDEO_FORMAT","The URL must end in .mp4 or .mov.")
    async with httpx.AsyncClient(follow_redirects=False,timeout=60) as client:
        resp=await client.get(url)
        if resp.status_code!=200: raise EngineError("URL_FETCH_FAILED",f"Video URL returned HTTP {resp.status_code}.",retryable=resp.status_code>=500)
        if len(resp.content)>settings.max_upload_mb*1024*1024: raise EngineError("UPLOAD_TOO_LARGE",f"Maximum download size is {settings.max_upload_mb} MB.")
    path=settings.data_dir/"videos"/f"{uuid.uuid4()}{ext}";path.write_bytes(resp.content)
    record=_video_record(path,Path(parsed.path).name,rights_confirmed)
    response={"video":record,"message":"Video downloaded and inspected."};_store_idem(key,digest,response);return response

@app.post("/api/v1/sessions")
async def create_session(request: Request, payload: SessionCreate):
    key,digest=_idem(request,payload.model_dump())
    cached=_check_idem(key,digest)
    if cached:return cached
    video=VIDEOS.get(payload.video_id)
    if not video: raise HTTPException(404,{"code":"VIDEO_NOT_FOUND","message":"Video not found."})
    words=[w.model_dump() for w in payload.transcript]
    for w in words:
        if w["end"]>video["duration_s"]+0.05: raise EngineError("TRANSCRIPT_OUT_OF_RANGE","Transcript contains a word outside the source video.",details={"word_id":w["word_id"]})
    sid=str(uuid.uuid4())
    tl=new_timeline(video["video_id"],video["duration_s"],video["fps_num"]/video["fps_den"],video["has_audio"],video["source_sha256"])
    session={"session_id":sid,"video_id":video["video_id"],"transcript":words,"timeline":tl,"pending":None,"created_at":time.time()}
    SESSIONS[sid]=session
    response={"session_id":sid,"video_id":video["video_id"],"duration_s":video["duration_s"],"transcript_words":len(words),"timeline_hash":timeline_hash(tl)}
    _store_idem(key,digest,response);return response

def _run_transcription(job_id: str, video_id: str, correlation_id: str | None=None):
    logger.info(json.dumps({"timestamp":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"level":"INFO","job_id":job_id,"correlation_id":correlation_id,"event":"transcription_started"}))
    job=JOBS[job_id];job.update({"status":"running","progress":10})
    try:
        provider=get_provider();video=VIDEOS[video_id]
        words=provider.transcribe(Path(video["path"]))
        job.update({"status":"succeeded","progress":100,"result":{"provider":provider.name,"word_count":len(words),"words":words}})
        logger.info(json.dumps({"timestamp":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"level":"INFO","job_id":job_id,"correlation_id":correlation_id,"event":"transcription_succeeded","word_count":len(words)}))
    except TranscriptionUnavailable as e:
        job.update({"status":"failed","progress":100,"error":{"code":"TRANSCRIPTION_PROVIDER_UNAVAILABLE","message":str(e),"retryable":False,"details":{}}})
        logger.warning(json.dumps({"timestamp":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"level":"WARNING","job_id":job_id,"correlation_id":correlation_id,"event":"transcription_failed","code":"TRANSCRIPTION_PROVIDER_UNAVAILABLE"}))
    except Exception as e:
        job.update({"status":"failed","progress":100,"error":{"code":"TRANSCRIPTION_FAILED","message":str(e),"retryable":False,"details":{}}})
        logger.error(json.dumps({"timestamp":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"level":"ERROR","job_id":job_id,"correlation_id":correlation_id,"event":"transcription_failed"}))

@app.post("/api/v1/videos/{video_id}/transcribe",status_code=202)
async def transcribe_video(request: Request, background_tasks: BackgroundTasks, video_id: str):
    key,digest=_idem(request,{"video_id":video_id,"action":"transcribe"})
    cached=_check_idem(key,digest)
    if cached:return JSONResponse(status_code=202,content=cached)
    if video_id not in VIDEOS: raise HTTPException(404,{"code":"VIDEO_NOT_FOUND","message":"Video not found."})
    job_id=str(uuid.uuid4());JOBS[job_id]={"job_id":job_id,"status":"queued","progress":0,"result":None,"error":None}
    response={"job_id":job_id,"status":"queued","progress":0}
    _store_idem(key,digest,response);background_tasks.add_task(_run_transcription,job_id,video_id,request.state.correlation_id)
    return JSONResponse(status_code=202,content=response)

@app.get("/api/v1/videos/{video_id}")
async def get_video(video_id: str):
    video=VIDEOS.get(video_id)
    if not video: raise HTTPException(404,{"code":"VIDEO_NOT_FOUND","message":"Video not found."})
    return {k:v for k,v in video.items() if k!="path"}

@app.get("/api/v1/sessions/{session_id}/timeline")
async def get_timeline(session_id: str):
    session=SESSIONS.get(session_id)
    if not session: raise HTTPException(404,{"code":"SESSION_NOT_FOUND","message":"Session not found."})
    tl=session["timeline"]
    return {"timeline":tl,"timeline_hash":timeline_hash(tl),"duration_s":duration(tl)}

@app.get("/api/v1/sessions/{session_id}/otio")
async def get_session_otio(session_id: str, download: bool = False):
    session=SESSIONS.get(session_id)
    if not session: raise HTTPException(404,{"code":"SESSION_NOT_FOUND","message":"Session not found."})
    video=VIDEOS.get(session.get("video_id"))
    filename=video.get("filename") if video else None
    otio_data=export_otio(session["timeline"],video_filename=filename)
    if download:
        return JSONResponse(content=otio_data,headers={"Content-Disposition":f"attachment; filename=incuedit_{session_id}.otio"})
    return otio_data

@app.get("/api/v1/sessions/{session_id}/transcript")
async def get_transcript(session_id: str):
    session=SESSIONS.get(session_id)
    if not session: raise HTTPException(404,{"code":"SESSION_NOT_FOUND","message":"Session not found."})
    return {"words":session["transcript"]}

@app.post("/api/v1/sessions/{session_id}/instructions")
async def apply_instruction(request: Request, session_id: str, payload: InstructionRequest):
    key,digest=_idem(request,{"session_id":session_id,**payload.model_dump()})
    cached=_check_idem(key,digest)
    if cached:return cached
    session=SESSIONS.get(session_id)
    if not session: raise HTTPException(404,{"code":"SESSION_NOT_FOUND","message":"Session not found."})
    result=engine.apply(session,payload.say,payload.answer)
    result["session_id"]=session_id
    _store_idem(key,digest,result)
    return result

@app.post("/api/v1/sessions/{session_id}/restore")
async def restore_snapshot(request: Request, session_id: str, payload: RestoreRequest):
    key,digest=_idem(request,{"session_id":session_id,**payload.model_dump()})
    cached=_check_idem(key,digest)
    if cached:return cached
    session=SESSIONS.get(session_id)
    if not session: raise HTTPException(404,{"code":"SESSION_NOT_FOUND","message":"Session not found."})
    tl=session["timeline"]; history=tl.get("history",[])
    if payload.history_index is None or not 0<=payload.history_index<len(history): raise EngineError("HISTORY_ENTRY_NOT_FOUND","The requested history entry does not exist.",details={"history_count":len(history)})
    target=history[payload.history_index]
    before=tl
    restored={k:v for k,v in target["timeline"].items()}
    restored["history"]=[*history[:payload.history_index],{"label":"restore snapshot","timeline":{k:v for k,v in tl.items() if k not in {"history","redo"}}}]
    restored["redo"]=[]
    session["timeline"]=restored
    response={"status":"applied","operations":[{"type":"restore_snapshot","history_index":payload.history_index,"label":target.get("label")}],"summary":{"message":"Restored the selected historical timeline snapshot.","before_duration_s":round(duration(before),3),"after_duration_s":round(duration(restored),3),"time_policy":"current_timeline"},"question":None,"options":[],"timeline_hash":timeline_hash(restored),"duration_s":round(duration(restored),3)}
    _store_idem(key,digest,response);return response

@app.get("/api/v1/sessions/{session_id}/history")
async def get_session_history(session_id: str):
    session = SESSIONS.get(session_id)
    if not session: raise HTTPException(404, {"code": "SESSION_NOT_FOUND", "message": "Session not found."})
    tl = session["timeline"]
    return {
        "session_id": session_id,
        "history": tl.get("history", []),
        "redo": tl.get("redo", []),
        "timeline_hash": timeline_hash(tl)
    }

@app.post("/api/v1/sessions/{session_id}/undo")
async def undo_session(request: Request, session_id: str):
    key, digest = _idem(request, {"session_id": session_id, "action": "undo"})
    cached = _check_idem(key, digest)
    if cached: return cached
    session = SESSIONS.get(session_id)
    if not session: raise HTTPException(404, {"code": "SESSION_NOT_FOUND", "message": "Session not found."})
    result = engine.apply(session, "Undo")
    result["session_id"] = session_id
    _store_idem(key, digest, result)
    return result

@app.post("/api/v1/sessions/{session_id}/redo")
async def redo_session(request: Request, session_id: str):
    key, digest = _idem(request, {"session_id": session_id, "action": "redo"})
    cached = _check_idem(key, digest)
    if cached: return cached
    session = SESSIONS.get(session_id)
    if not session: raise HTTPException(404, {"code": "SESSION_NOT_FOUND", "message": "Session not found."})
    result = engine.apply(session, "Redo")
    result["session_id"] = session_id
    _store_idem(key, digest, result)
    return result

@app.post("/api/v1/sessions/{session_id}/music")
async def upload_music(request: Request, session_id: str, file: UploadFile=File(...), rights_confirmed: bool=Form(False)):
    key,digest=_idem(request,{"session_id":session_id,"filename":file.filename,"size":file.size,"rights_confirmed":rights_confirmed})
    cached=_check_idem(key,digest)
    if cached:return cached
    session=SESSIONS.get(session_id)
    if not session: raise HTTPException(404,{"code":"SESSION_NOT_FOUND","message":"Session not found."})
    if not rights_confirmed: raise EngineError("RIGHTS_CONFIRMATION_REQUIRED","Confirm that you own or have a commercial-use licence for this music track.")
    ext=Path(file.filename or "music.mp3").suffix.lower()
    if ext not in {".mp3",".wav",".m4a",".aac",".flac"}: raise EngineError("UNSUPPORTED_AUDIO_FORMAT","Music must be MP3, WAV, M4A, AAC, or FLAC.")
    data=await file.read(100*1024*1024+1)
    if len(data)>100*1024*1024: raise EngineError("MUSIC_TOO_LARGE","Music file exceeds 100 MB.")
    path=settings.data_dir/"videos"/f"{uuid.uuid4()}{ext}";path.write_bytes(data)
    before=clone(session["timeline"]);after=clone(before)
    after["music"]={"path":str(path.resolve()),"filename":file.filename,"asset_sha256":sha256_file(path),"active":False,"duck_under_speech":True,"rights":"user_attested"}
    after["history"]=deepcopy(before.get("history",[]))+[{"label":"upload background music asset","timeline":{k:v for k,v in before.items() if k not in {"history","redo"}}}]
    after["redo"]=[];session["timeline"]=after
    response={"status":"uploaded","filename":file.filename,"message":"Music uploaded. Say 'add background music' to apply it with speech ducking."}
    _store_idem(key,digest,response);return response

def _run_render(job_id: str, session_id: str, correlation_id: str | None=None):
    logger.info(json.dumps({"timestamp":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"level":"INFO","job_id":job_id,"correlation_id":correlation_id,"event":"render_started"}))
    job=JOBS[job_id];job.update({"status":"running","progress":5})
    try:
        session=SESSIONS[session_id];video=VIDEOS[session["video_id"]]
        out=settings.data_dir/"renders"/f"{job_id}.mp4";manifest=settings.data_dir/"renders"/f"{job_id}.manifest.json"
        job["progress"]=20
        result=render_timeline(Path(video["path"]),session["timeline"],session["transcript"],out,manifest)
        s3_video=upload_output(out,f"renders/{job_id}.mp4","video/mp4")
        s3_manifest=upload_output(manifest,f"renders/{job_id}.manifest.json","application/json")
        job.update({"status":"succeeded","progress":100,"result":{"video_url":s3_video or f"/api/v1/jobs/{job_id}/video","manifest_url":s3_manifest or f"/api/v1/jobs/{job_id}/manifest","local_video_url":f"/api/v1/jobs/{job_id}/video","manifest":result}})
        logger.info(json.dumps({"timestamp":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"level":"INFO","job_id":job_id,"correlation_id":correlation_id,"event":"render_succeeded","timeline_hash":result.get("timeline_hash")}))
    except EngineError as e:
        job.update({"status":"failed","progress":100,"error":{"code":e.code,"message":e.message,"retryable":e.retryable,"details":e.details}})
        logger.error(json.dumps({"timestamp":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"level":"ERROR","job_id":job_id,"correlation_id":correlation_id,"event":"render_failed","code":e.code}))
    except Exception as e:
        job.update({"status":"failed","progress":100,"error":{"code":"INTERNAL_RENDER_ERROR","message":str(e),"retryable":False,"details":{}}})
        logger.error(json.dumps({"timestamp":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"level":"ERROR","job_id":job_id,"correlation_id":correlation_id,"event":"render_failed","code":"INTERNAL_RENDER_ERROR"}))
    
    cb_url = job.get("callback_url")
    if cb_url:
        try:
            body = json.dumps(job, default=str)
            sig = hmac.new(settings.webhook_secret.encode(), body.encode(), hashlib.sha256).hexdigest()
            with httpx.Client(timeout=10) as client:
                client.post(cb_url, content=body, headers={"Content-Type": "application/json", "X-IncuBrix-Signature": f"sha256={sig}"})
            logger.info(json.dumps({"timestamp":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"level":"INFO","job_id":job_id,"correlation_id":correlation_id,"event":"webhook_dispatched","target":cb_url}))
        except Exception as exc:
            logger.warning(json.dumps({"timestamp":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"level":"WARNING","job_id":job_id,"correlation_id":correlation_id,"event":"webhook_failed","error":str(exc)}))

@app.post("/api/v1/sessions/{session_id}/render",status_code=202)
async def render_session(request: Request, background_tasks: BackgroundTasks, session_id: str, payload: RenderRequest | None = None):
    cb = payload.callback_url if payload else None
    key,digest=_idem(request,{"session_id":session_id,"action":"render","callback_url":cb})
    cached=_check_idem(key,digest)
    if cached:return JSONResponse(status_code=202,content=cached)
    if session_id not in SESSIONS: raise HTTPException(404,{"code":"SESSION_NOT_FOUND","message":"Session not found."})
    job_id=str(uuid.uuid4());JOBS[job_id]={"job_id":job_id,"status":"queued","progress":0,"result":None,"error":None,"callback_url":cb}
    response={"job_id":job_id,"status":"queued","progress":0}
    _store_idem(key,digest,response);background_tasks.add_task(_run_render,job_id,session_id,getattr(request.state,"correlation_id",None))
    return JSONResponse(status_code=202,content=response)

@app.get("/api/v1/jobs/{job_id}")
async def get_job(job_id: str):
    job=JOBS.get(job_id)
    if not job: raise HTTPException(404,{"code":"JOB_NOT_FOUND","message":"Job not found."})
    return job

@app.get("/api/v1/jobs/{job_id}/video")
async def get_job_video(job_id: str):
    path=settings.data_dir/"renders"/f"{job_id}.mp4"
    if not path.exists(): raise HTTPException(404,{"code":"OUTPUT_NOT_FOUND","message":"Rendered video is not ready."})
    return FileResponse(path,media_type="video/mp4",filename=f"incuedit_{job_id}.mp4")

@app.get("/api/v1/jobs/{job_id}/manifest")
async def get_job_manifest(job_id: str):
    path=settings.data_dir/"renders"/f"{job_id}.manifest.json"
    if not path.exists(): raise HTTPException(404,{"code":"MANIFEST_NOT_FOUND","message":"Render manifest is not ready."})
    return FileResponse(path,media_type="application/json",filename="manifest.json")
