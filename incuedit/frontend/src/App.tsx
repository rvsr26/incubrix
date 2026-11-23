import React, { useState, useEffect, useRef } from 'react';
import { Word, VideoMetadata, Timeline, InstructionResponse } from './types';

const API_BASE = (typeof window !== 'undefined' && window.location.port && window.location.port !== '8000')
  ? 'http://localhost:8000'
  : '';

export default function App() {
  const [video, setVideo] = useState<VideoMetadata | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [timeline, setTimeline] = useState<Timeline | null>(null);
  const [durationS, setDurationS] = useState<number>(0);
  const [timelineHash, setTimelineHash] = useState<string>('');
  const [transcript, setTranscript] = useState<Word[]>([]);
  const [transcriptJson, setTranscriptJson] = useState<string>('');
  const [prompt, setPrompt] = useState<string>('');
  const [lastResponse, setLastResponse] = useState<InstructionResponse | null>(null);
  const [clarifyAnswer, setClarifyAnswer] = useState<string>('');
  const [rightsConfirmed, setRightsConfirmed] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(false);
  const [renderJob, setRenderJob] = useState<any>(null);
  const [apiOnline, setApiOnline] = useState<boolean>(false);

  const videoRef = useRef<HTMLVideoElement>(null);
  const renderVideoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/health`)
      .then(r => r.json())
      .then(() => setApiOnline(true))
      .catch(() => setApiOnline(false));

    // Load sample transcript by default
    const sampleWords: Word[] = [
      { word_id: "w001", text: "Welcome", start: 0.3, end: 0.75, speaker: "host", confidence: 0.99 },
      { word_id: "w002", text: "to", start: 0.77, end: 0.91, speaker: "host", confidence: 0.98 },
      { word_id: "w003", text: "the", start: 0.92, end: 1.05, speaker: "host", confidence: 0.99 },
      { word_id: "w004", text: "channel.", start: 1.07, end: 1.65, speaker: "host", confidence: 0.99 },
      { word_id: "w005", text: "Today", start: 2.3, end: 2.7, speaker: "host", confidence: 0.98 },
      { word_id: "w006", text: "we", start: 2.72, end: 2.86, speaker: "host", confidence: 0.98 },
      { word_id: "w007", text: "will", start: 2.88, end: 3.1, speaker: "host", confidence: 0.97 },
      { word_id: "w008", text: "discuss", start: 3.12, end: 3.6, speaker: "host", confidence: 0.98 },
      { word_id: "w009", text: "pricing", start: 7.5, end: 8.1, speaker: "host", confidence: 0.99 },
      { word_id: "w010", text: "and", start: 8.12, end: 8.28, speaker: "host", confidence: 0.98 },
      { word_id: "w011", text: "cost.", start: 8.3, end: 8.7, speaker: "host", confidence: 0.98 },
      { word_id: "w012", text: "Thanks", start: 12.0, end: 12.4, speaker: "guest", confidence: 0.94 }
    ];
    setTranscript(sampleWords);
    setTranscriptJson(JSON.stringify(sampleWords, null, 2));
  }, []);

  const refreshTimeline = async (sid: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/sessions/${sid}/timeline`);
      const data = await res.json();
      if (res.ok) {
        setTimeline(data.timeline);
        setDurationS(data.duration_s);
        setTimelineHash(data.timeline_hash);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    const fd = new FormData();
    fd.append('file', file);
    fd.append('rights_confirmed', String(rightsConfirmed));

    try {
      const res = await fetch(`${API_BASE}/api/v1/videos/upload`, {
        method: 'POST',
        headers: { 'Idempotency-Key': crypto.randomUUID() },
        body: fd
      });
      const data = await res.json();
      if (res.ok) {
        setVideo(data.video);
        if (videoRef.current) {
          videoRef.current.src = URL.createObjectURL(file);
        }
      } else {
        alert(data.error?.message || 'Upload failed');
      }
    } catch (err: any) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSession = async () => {
    if (!video) return;
    try {
      const parsedWords = JSON.parse(transcriptJson);
      const res = await fetch(`${API_BASE}/api/v1/sessions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Idempotency-Key': crypto.randomUUID()
        },
        body: JSON.stringify({ video_id: video.video_id, transcript: parsedWords })
      });
      const data = await res.json();
      if (res.ok) {
        setSessionId(data.session_id);
        setTranscript(parsedWords);
        refreshTimeline(data.session_id);
      } else {
        alert(data.error?.message || 'Create session failed');
      }
    } catch (e: any) {
      alert('Invalid transcript JSON: ' + e.message);
    }
  };

  const sendInstruction = async (text: string, answer?: string) => {
    if (!sessionId) return;
    const say = text || prompt;
    if (!say && !answer) return;

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/sessions/${sessionId}/instructions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Idempotency-Key': crypto.randomUUID()
        },
        body: JSON.stringify({ say, answer })
      });
      const data: InstructionResponse = await res.json();
      setLastResponse(data);
      if (data.status === 'applied') {
        setPrompt('');
      }
      refreshTimeline(sessionId);
    } catch (err: any) {
      setLastResponse({
        status: 'rejected',
        operations: [],
        summary: { message: err.message },
        timeline_hash: timelineHash,
        duration_s: durationS
      });
    } finally {
      setLoading(false);
    }
  };

  const handleRender = async () => {
    if (!sessionId) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/sessions/${sessionId}/render`, {
        method: 'POST',
        headers: { 'Idempotency-Key': crypto.randomUUID() }
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error?.message || 'Render failed');
      
      const jobId = data.job_id;
      for (let i = 0; i < 300; i++) {
        await new Promise(r => setTimeout(r, 1000));
        const jRes = await fetch(`${API_BASE}/api/v1/jobs/${jobId}`);
        const jData = await jRes.json();
        setRenderJob(jData);
        if (jData.status === 'succeeded' || jData.status === 'failed') break;
      }
    } catch (err: any) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '1440px', margin: '0 auto', padding: '24px' }}>
      {/* Header */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', borderBottom: '1px solid #1e293b', paddingBottom: '16px' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 800, color: '#f8fafc', margin: 0 }}>IncuEdit Studio</h1>
          <p style={{ fontSize: '13px', color: '#94a3b8', margin: '4px 0 0 0' }}>Prompt-Based Reversible Video Editing Engine</p>
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <span style={{ fontSize: '12px', padding: '4px 10px', borderRadius: '16px', background: apiOnline ? '#064e3b' : '#7f1d1d', color: apiOnline ? '#34d399' : '#f87171' }}>
            {apiOnline ? '● API Online' : '● API Offline'}
          </span>
          {sessionId && (
            <a href={`/api/v1/sessions/${sessionId}/otio?download=true`} target="_blank" rel="noreferrer" style={{ fontSize: '12px', padding: '6px 12px', borderRadius: '6px', background: '#1e293b', color: '#e2e8f0', textDecoration: 'none' }}>
              Export OTIO
            </a>
          )}
        </div>
      </header>

      {/* Main Studio Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '24px' }}>
        {/* Left: Video Player & Transcripts */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Video Intake */}
          <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', padding: '20px' }}>
            <h2 style={{ fontSize: '16px', fontWeight: 700, margin: '0 0 12px 0' }}>1. Source Media</h2>
            <input type="file" accept="video/mp4,video/quicktime,.mp4,.mov" onChange={handleUpload} style={{ marginBottom: '10px' }} />
            <label style={{ display: 'flex', gap: '8px', fontSize: '12px', color: '#94a3b8', margin: '8px 0', cursor: 'pointer' }}>
              <input type="checkbox" checked={rightsConfirmed} onChange={e => setRightsConfirmed(e.target.checked)} />
              <span>I own or have permission to process this media for assessment evaluation.</span>
            </label>
            <div style={{ background: '#000', borderRadius: '8px', overflow: 'hidden', aspectRatio: '16/9', display: 'grid', placeItems: 'center', marginTop: '10px' }}>
              <video ref={videoRef} controls style={{ width: '100%', height: '100%' }} />
            </div>
            {video && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px', marginTop: '12px' }}>
                <div style={{ background: '#1e293b', padding: '8px', borderRadius: '6px', textAlign: 'center' }}>
                  <div style={{ fontSize: '14px', fontWeight: 700, color: '#60a5fa' }}>{video.duration_s.toFixed(1)}s</div>
                  <div style={{ fontSize: '10px', color: '#94a3b8' }}>Duration</div>
                </div>
                <div style={{ background: '#1e293b', padding: '8px', borderRadius: '6px', textAlign: 'center' }}>
                  <div style={{ fontSize: '14px', fontWeight: 700, color: '#60a5fa' }}>{video.fps.toFixed(2)}</div>
                  <div style={{ fontSize: '10px', color: '#94a3b8' }}>FPS</div>
                </div>
                <div style={{ background: '#1e293b', padding: '8px', borderRadius: '6px', textAlign: 'center' }}>
                  <div style={{ fontSize: '14px', fontWeight: 700, color: '#60a5fa' }}>{video.width}x{video.height}</div>
                  <div style={{ fontSize: '10px', color: '#94a3b8' }}>Resolution</div>
                </div>
                <div style={{ background: '#1e293b', padding: '8px', borderRadius: '6px', textAlign: 'center' }}>
                  <div style={{ fontSize: '14px', fontWeight: 700, color: '#60a5fa' }}>{video.has_audio ? 'Stereo' : 'None'}</div>
                  <div style={{ fontSize: '10px', color: '#94a3b8' }}>Audio</div>
                </div>
              </div>
            )}
          </div>

          {/* Transcript Alignment */}
          <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <h2 style={{ fontSize: '16px', fontWeight: 700, margin: 0 }}>2. Word-Level Transcript</h2>
              <button onClick={handleCreateSession} disabled={!video || loading} style={{ background: '#3b82f6', color: '#fff', border: 0, padding: '8px 14px', borderRadius: '6px', fontWeight: 600, cursor: 'pointer' }}>
                Create Session
              </button>
            </div>
            <textarea value={transcriptJson} onChange={e => setTranscriptJson(e.target.value)} style={{ width: '100%', minHeight: '120px', background: '#020617', border: '1px solid #1e293b', color: '#e2e8f0', borderRadius: '6px', padding: '8px', fontFamily: 'monospace', fontSize: '11px' }} />
            {/* Word clickable pills */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '10px', maxHeight: '140px', overflowY: 'auto' }}>
              {transcript.map((w, idx) => (
                <span key={idx} onClick={() => { if (videoRef.current) { videoRef.current.currentTime = w.start; videoRef.current.play(); } }} style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '4px', padding: '2px 6px', fontSize: '11px', cursor: 'pointer' }}>
                  {w.text} ({w.start.toFixed(1)}s)
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Right: Prompt Engine, Visual Timeline & History */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Prompt Console */}
          <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', padding: '20px' }}>
            <h2 style={{ fontSize: '16px', fontWeight: 700, margin: '0 0 12px 0' }}>3. Editing Prompt Console</h2>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
              <input type="text" value={prompt} onChange={e => setPrompt(e.target.value)} onKeyDown={e => e.key === 'Enter' && sendInstruction(prompt)} placeholder="Type edit command (e.g. Cut the first 2 seconds)..." disabled={!sessionId || loading} style={{ flex: 1, background: '#020617', border: '1px solid #1e293b', color: '#f8fafc', borderRadius: '6px', padding: '10px' }} />
              <button onClick={() => sendInstruction(prompt)} disabled={!sessionId || loading} style={{ background: '#3b82f6', color: '#fff', border: 0, padding: '10px 18px', borderRadius: '6px', fontWeight: 600, cursor: 'pointer' }}>
                Apply
              </button>
            </div>

            {/* Quick Prompt Chips */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '12px' }}>
              {["Cut the first 2 seconds", "Add a caption 'Welcome!' when I say welcome", "Remove all filler words", "Make that caption red", "Speed up from 2 to 4 by 2x", "Put the intro back", "Undo"].map((chipText, i) => (
                <button key={i} onClick={() => sendInstruction(chipText)} disabled={!sessionId || loading} style={{ background: '#1e293b', border: '1px solid #334155', color: '#94a3b8', borderRadius: '14px', padding: '4px 10px', fontSize: '11px', cursor: 'pointer' }}>
                  {chipText}
                </button>
              ))}
            </div>

            {/* Clarification Box */}
            {lastResponse?.status === 'needs_clarification' && (
              <div style={{ background: '#1c1917', border: '1px solid #854d0e', borderRadius: '8px', padding: '12px', marginBottom: '12px' }}>
                <div style={{ fontSize: '13px', fontWeight: 700, color: '#fde047', marginBottom: '8px' }}>{lastResponse.question}</div>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '8px' }}>
                  {lastResponse.options?.map((opt, i) => (
                    <button key={i} onClick={() => sendInstruction(prompt, String(opt.id || opt.label))} style={{ background: '#78350f', color: '#fff', border: 0, padding: '4px 10px', borderRadius: '4px', fontSize: '11px', cursor: 'pointer' }}>
                      {opt.label}
                    </button>
                  ))}
                </div>
                <div style={{ display: 'flex', gap: '6px' }}>
                  <input type="text" value={clarifyAnswer} onChange={e => setClarifyAnswer(e.target.value)} placeholder="Type answer (e.g. 'the second one', 'all')..." style={{ flex: 1, background: '#020617', border: '1px solid #78350f', color: '#f8fafc', padding: '6px', borderRadius: '4px', fontSize: '12px' }} />
                  <button onClick={() => sendInstruction(prompt, clarifyAnswer)} style={{ background: '#ca8a04', color: '#000', border: 0, padding: '6px 12px', borderRadius: '4px', fontWeight: 600, fontSize: '12px', cursor: 'pointer' }}>Submit</button>
                </div>
              </div>
            )}

            {/* Response Card */}
            {lastResponse && (
              <div style={{ background: lastResponse.status === 'applied' ? '#064e3b22' : lastResponse.status === 'needs_clarification' ? '#78350f22' : '#7f1d1d22', border: `1px solid ${lastResponse.status === 'applied' ? '#059669' : lastResponse.status === 'needs_clarification' ? '#d97706' : '#dc2626'}`, borderRadius: '8px', padding: '12px', marginBottom: '12px' }}>
                <span style={{ fontSize: '10px', fontWeight: 800, textTransform: 'uppercase', padding: '2px 6px', borderRadius: '4px', background: lastResponse.status === 'applied' ? '#064e3b' : lastResponse.status === 'needs_clarification' ? '#78350f' : '#7f1d1d', color: lastResponse.status === 'applied' ? '#34d399' : lastResponse.status === 'needs_clarification' ? '#fbbf24' : '#f87171' }}>
                  {lastResponse.status.replace('_', ' ')}
                </span>
                <p style={{ fontSize: '13px', margin: '8px 0 0 0', color: '#f1f5f9' }}>{lastResponse.summary?.message}</p>
              </div>
            )}

            {/* Visual Timeline Track */}
            <div style={{ background: '#020617', border: '1px solid #1e293b', borderRadius: '8px', padding: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#94a3b8', marginBottom: '6px' }}>
                <span>Timeline Decision Slices ({timeline?.segments.length || 0})</span>
                <span style={{ color: '#60a5fa', fontWeight: 700 }}>{durationS.toFixed(2)}s</span>
              </div>
              <div style={{ display: 'flex', height: '24px', background: '#1e293b', borderRadius: '4px', overflow: 'hidden', gap: '2px', padding: '2px' }}>
                {timeline?.segments.map((seg, idx) => (
                  <div key={idx} style={{ flex: seg.source_end - seg.source_start, background: 'linear-gradient(90deg, #3b82f6, #6366f1)', borderRadius: '2px' }} title={`Seg ${idx+1}: ${seg.source_start.toFixed(2)}s - ${seg.source_end.toFixed(2)}s (${seg.speed}x)`} />
                ))}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: '#64748b', marginTop: '4px' }}>
                <span>0.00s</span>
                <span>Hash: {timelineHash.slice(0, 8)}</span>
                <span>{durationS.toFixed(2)}s</span>
              </div>
            </div>
          </div>

          {/* Render & History */}
          <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <h2 style={{ fontSize: '16px', fontWeight: 700, margin: 0 }}>4. Export & History</h2>
              <div style={{ display: 'flex', gap: '6px' }}>
                <button onClick={() => sendInstruction('Undo')} disabled={!timeline?.history?.length} style={{ background: '#1e293b', color: '#f1f5f9', border: '1px solid #334155', padding: '6px 12px', borderRadius: '4px', fontSize: '12px', cursor: 'pointer' }}>Undo</button>
                <button onClick={() => sendInstruction('Redo')} disabled={!timeline?.redo?.length} style={{ background: '#1e293b', color: '#f1f5f9', border: '1px solid #334155', padding: '6px 12px', borderRadius: '4px', fontSize: '12px', cursor: 'pointer' }}>Redo</button>
                <button onClick={handleRender} disabled={!sessionId || loading} style={{ background: '#10b981', color: '#fff', border: 0, padding: '6px 14px', borderRadius: '4px', fontWeight: 600, fontSize: '12px', cursor: 'pointer' }}>Render MP4</button>
              </div>
            </div>

            {/* Render Preview */}
            {renderJob?.status === 'succeeded' && (
              <div style={{ marginTop: '12px' }}>
                <div style={{ background: '#000', borderRadius: '8px', overflow: 'hidden', aspectRatio: '16/9', display: 'grid', placeItems: 'center' }}>
                  <video ref={renderVideoRef} src={renderJob.result?.video_url ? (renderJob.result.video_url.startsWith('http') ? renderJob.result.video_url : `${API_BASE}${renderJob.result.video_url}`) : undefined} controls style={{ width: '100%', height: '100%' }} />
                </div>
                <div style={{ display: 'flex', gap: '10px', marginTop: '8px' }}>
                  <a href={renderJob.result?.video_url ? (renderJob.result.video_url.startsWith('http') ? renderJob.result.video_url : `${API_BASE}${renderJob.result.video_url}`) : '#'} download="rendered_output.mp4" style={{ fontSize: '12px', padding: '6px 12px', borderRadius: '6px', background: '#3b82f6', color: '#fff', textDecoration: 'none' }}>Download MP4</a>
                  <a href={renderJob.result?.manifest_url ? (renderJob.result.manifest_url.startsWith('http') ? renderJob.result.manifest_url : `${API_BASE}${renderJob.result.manifest_url}`) : '#'} target="_blank" rel="noreferrer" style={{ fontSize: '12px', padding: '6px 12px', borderRadius: '6px', background: '#1e293b', color: '#e2e8f0', textDecoration: 'none' }}>View Manifest</a>
                </div>
              </div>
            )}

            {/* History Snapshot Stack */}
            <div style={{ marginTop: '14px', maxHeight: '160px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {timeline?.history?.slice().reverse().map((h, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#020617', border: '1px solid #1e293b', padding: '6px 10px', borderRadius: '4px', fontSize: '11px' }}>
                  <span><b>#{timeline.history!.length - i}</b> {h.label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
