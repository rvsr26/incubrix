# IncuEdit — Final Candidate Submission Checklist

**Deadline:** Today, 23 November 2026, by 11:59 PM IST  
**Candidate:** RAJALA VISHNU SATHWICK REDDY  
**Application Track:** Software Engineer  
**Problem Statement:** PS2 — Prompt-Based Video Editing Engine  

---

Follow this prioritized checklist step-by-step to complete your official IncuBrix submission:

---

### Step 1: Personally Sign Your Assessment Workbook
> [!IMPORTANT]
> The automated system has verified the entire workbook but intentionally left Sheet `7_Declaration` completely blank so that you can personally review and sign it.

1. Open `Assessment2_Rajala_Vishnu_Sathwick_Reddy_FINAL.xlsx` in Excel or LibreOffice.
2. Navigate to sheet **`7_Declaration`**.
3. Review statements 1 through 8 (rows 4 to 11).
4. Enter **`Yes`** in column B for each statement (cells `B4:B11`).
5. In cell **`B12`**, type your full legal name as signature: `RAJALA VISHNU SATHWICK REDDY`.
6. In cell **`B13`**, enter today's date: `23 November 2026`.
7. Save the file.
8. (Also save a copy inside `incuedit/Assessment2_Rajala_Vishnu_Sathwick_Reddy_FINAL.xlsx`).

---

### Step 2: Record the 8-Minute Demo Video
1. Open [DEMO_RECORDING_SCRIPT.md](file:///c:/Users/Vishnu/Downloads/incubrix/DEMO_RECORDING_SCRIPT.md).
2. Start the local server:
   ```bash
   cd incuedit
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
3. Open your browser to `http://localhost:8000/app/`.
4. Use OBS Studio, Windows Game Bar (`Win + G`), or Loom to record your screen and microphone.
5. Follow the exact 8-minute timeline:
   - **0:00–0:30:** Introduce yourself, IncuEdit, and the problem statement.
   - **0:30–1:15:** Upload `examples/demo_media.mp4` and inspect video metadata.
   - **1:15–2:15:** Inspect transcript and show how word IDs provide stable content anchors.
   - **2:15–3:30:** Apply cuts, captions, and bleeps; demonstrate that captions stick to words.
   - **3:30–4:15:** Enter an ambiguous command (e.g. "remove after thanks") and show clarification response.
   - **4:15–5:00:** Demonstrate undo, redo, and restoring an earlier edit version.
   - **5:00–6:15:** Click Render Video, show real-time async job polling and manifest generation.
   - **6:15–7:00:** Play rendered video and inspect output manifest.
   - **7:00–7:45:** Show passing test suite in terminal (`python -m pytest -q`) and one key architecture file (`app/timeline.py`).
   - **7:45–8:00:** Conclude.
6. Upload the video to **YouTube as Unlisted** (or Google Drive with "Anyone with the link can view").
7. Copy the public share link.

---

### Step 3: Grant GitHub Repository Access
1. Open your repository: [https://github.com/rvsr26/incubrix](https://github.com/rvsr26/incubrix).
2. Go to **Settings** → **Collaborators** (`https://github.com/rvsr26/incubrix/settings/access`).
3. Click **Add people**.
4. Enter `techteam@incubrix.com`.
5. Confirm the invitation with read/reviewer access.

---

### Step 4 (Optional): Deploy Public Live Demo
- If you wish to provide a public cloud demo link in addition to the verified local demo, follow [DEPLOYMENT_GUIDE.md](file:///c:/Users/Vishnu/Downloads/incubrix/DEPLOYMENT_GUIDE.md) to deploy to Render.com in ~5 minutes.
- If you prefer not to create external cloud accounts, use the honest response documented in `GOOGLE_FORM_ANSWERS.md`:
  *"Local demo verified at http://localhost:8000/app; cloud deployment guide provided."*

---

### Step 5: Fill the Official IncuBrix Google Form
1. Open the Google Form link provided in your IncuBrix invitation email.
2. Open [GOOGLE_FORM_ANSWERS.md](file:///c:/Users/Vishnu/Downloads/incubrix/GOOGLE_FORM_ANSWERS.md).
3. Copy and paste each verified answer into the corresponding form field:
   - Amrita Registration ID: Enter your real university ID.
   - Full Name: `RAJALA VISHNU SATHWICK REDDY`
   - Registered Email: `rajalavishnureddy@gmail.com`
   - Application Track: `Software Engineer`
   - Problem Statement: `PS2 — Prompt-Based Video Editing Engine`
   - Upload Form: Upload your signed `Assessment2_Rajala_Vishnu_Sathwick_Reddy_FINAL.xlsx`.
   - GitHub Repository URL: `https://github.com/rvsr26/incubrix`
   - Demo Video URL: Paste your YouTube / Google Drive video link from Step 2.
   - Self-Score & Outcome Summary: Copy directly from `GOOGLE_FORM_ANSWERS.md`.
4. Personally check the final declaration checkboxes in the Google Form.
5. Click **Submit**.

---

### Step 6: Reply to the Invitation Email
1. Open the invitation email thread from IncuBrix.
2. Write a professional reply:
   ```
   Dear IncuBrix Tech Team,

   Please find attached my completed assessment submission for Problem Statement 2 (IncuEdit — Prompt-Based Video Editing Engine):

   - Completed Submission Workbook: Assessment2_Rajala_Vishnu_Sathwick_Reddy_FINAL.xlsx (attached)
   - Verified Submission Package: IncuEdit_FINAL_SUBMISSION.zip (attached / Google Drive link: [INSERT LINK IF >25MB])
   - Private GitHub Repository: https://github.com/rvsr26/incubrix (collaborator access invited for techteam@incubrix.com)
   - Unedited Demo Video (max 8 min): [PASTE YOUR VIDEO LINK]
   - Live Studio Demo: Local setup verified on port 8000 (React 18 Studio at /app, Dark Studio at /)

   The Google Form has also been completed and submitted. All 110 automated tests, OpenAPI contract validations, and 3-round determinism checks pass cleanly.

   Thank you,
   Rajala Vishnu Sathwick Reddy
   B.Tech Computer Science and Engineering
   Amrita Vishwa Vidyapeetham, Coimbatore
   Phone: 9390934449 | Email: rajalavishnureddy@gmail.com
   ```
3. Attach `Assessment2_Rajala_Vishnu_Sathwick_Reddy_FINAL.xlsx` and `IncuEdit_FINAL_SUBMISSION.zip`.
4. Send the email before 11:59 PM IST tonight.
