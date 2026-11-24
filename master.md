# MASTER — SC First Bank AI Voice Agent POC (Sharpsys Project)

> The single source of truth for this POC. Every decision, step, file and status is tracked here.
> Owner: Karkavelraja · CEO: Javagal Srinath · COO / client contact: Harikrishnan Indrababu · Client: Harry
> **Current deliverable:** a Korean real-time voice agent (Streamlit, free on Streamlit Community Cloud via GitHub). **Due: within 24 h of 24 Nov 2026, 11:26 IST.**

---

## 0. Status log (newest first)

| Date (IST) | What changed |
|---|---|
| 2026-11-24 | 🎨 **Client-facing redesign.** Phone-style call screen (call / end / mute / captions), Korean-first labels, live captions, simple call summary. **Nothing technical is visible to the client**: no model names, vendor, settings, latency or JSON. Streamlit menus and badges are hidden. The AI is told never to reveal its technology ("SC제일은행 AI 상담 도우미" only). Team settings moved to a hidden **`?admin=1`** view protected by `ADMIN_PASSCODE`. Errors show a generic Korean message to the client. Tested: client view showed 0 technical words; the team view shows settings, ⚡ response time and the typed-message box. |
| 2026-11-24 | ✅ **Streamlit voice agent built and tested** (`sc-voice-agent/`). The session-key request was checked against a fake OpenAI server (model, voice, VAD, interruption on, result tool). The UI was tested by replaying real-time events: chat bubbles in Korean, ✋ interruption tag, response time (0.75 s shown), result card R1/S1. Layout fixed. **Not yet tested with a real OpenAI key or a real voice** (the sandbox can't reach OpenAI). |
| 2026-11-24 | 🧭 Decisions: (1) voice conversation, (2) Harry and our team will both talk to it, (3) **Streamlit UI on Streamlit Community Cloud from GitHub**, (4) due in 24 h. Engine: **OpenAI Realtime `gpt-realtime-2.1`** (speech-to-speech, WebRTC, built-in interruption handling, Korean). |
| 2026-11-24 | 🔄 **SCOPE CHANGE.** Javagal: no phone calling, a conversational agent is enough. Client (Harry, via COO Harikrishnan) needs **Korean** (even for a quick demo), **fluent**, **no lag**, and the agent must **handle interruptions** (barge-in). → Twilio and phone mode dropped. Focus moves to a browser-based real-time Korean **voice** agent with an on-screen chat transcript. Decision on the voice engine is pending (see section 11). |
| 2026-11-23 | ✅ Deployment target changed to **GitHub → Render Free + MongoDB Atlas Free (M0)**. Added `render.yaml`, `.gitignore`, MongoDB storage (`lib/store.js`), passcode lock for the public URL (`DEMO_PASSCODE`), `/healthz`, `/api/history`. Re-tested: passcode 401/200 ✓, mock call → R1 ✓, history saved ✓, falls back to memory if Atlas is unreachable ✓. (A real Atlas connection can't be tested here, so test it after deploy.) |
| 2026-11-23 | 📝 Paid items list prepared for Javagal (section 10). |
| 2026-11-23 | ✅ Tested offline against the fake Vapi: dial → ringing → in-progress → ended → R1/S1 result → RM COMPASS updated the to-do, contact log, slot and SMS preview. Screens checked in a browser. |
| 2026-11-23 | ✅ Code built: server, assistant (KO + EN script and guardrails), result mapper, RM COMPASS mock, call-center window, fake Vapi. |
| 2026-11-23 | master.md created. POC architecture decided (Vapi + Twilio + Node server + mock RM COMPASS). |

**NEXT ACTION:** Javagal buys OpenAI API credit (section 4) → you push to GitHub and deploy on Streamlit Cloud (section 3) → test in English → test in Korean → rehearse with a Korean speaker.

### Build progress
- [x] Engine chosen: OpenAI Realtime over WebRTC (lowest lag, native interruption)
- [x] Mic inside the Streamlit HTML component verified (iframe allows `microphone` + `autoplay`)
- [x] `prompts.py`: Korean and English script TM-MAT-01, 7 guardrails, FAQ answers, real-time rules (short turns, stop when interrupted), `save_call_result` tool
- [x] `app.py`: passcode gate, settings sidebar (language, voice, model, turn-taking speed), session key (API key stays on the server), customer panel
- [x] `voice_component.html`: start/end/mute, mic meter, live chat bubbles, interruption tag, response-time meter, typed-message backup, result card + JSON download
- [x] Local test with the fake OpenAI server and replayed events
- [x] Client-facing redesign: call screen, captions, summary; nothing technical shown; hidden admin view
- [ ] OpenAI API key with credit (Javagal)
- [ ] GitHub repo pushed
- [ ] Deployed on Streamlit Community Cloud with secrets
- [ ] Real test in English (rehearsal)
- [ ] Real test in Korean + 12-case checklist (section 6)
- [ ] Rehearsal with a Korean speaker; tune voice and turn-taking speed

---

## 1. What the client needs (from Harry, via Harikrishnan)

| Need | How the POC meets it |
|---|---|
| **Korean**, even for a quick demo | Korean is the default language. Polite honorific Korean script; Korean transcription |
| **Fluent** | Native speech-to-speech model (no separate text-to-speech step); natural voices (`marin` default) |
| **No lag** | WebRTC straight from the browser to OpenAI; short turns; adjustable silence threshold (default 450 ms). The **⚡ Response** meter shows the delay live |
| **Can be interrupted and picks it up** | Server voice detection with `interrupt_response: true`: the AI stops mid-sentence and answers the new input. The bubble is tagged **interrupted** |
| No phone calling (Javagal) | Browser mic and speaker only |

---

## 2. Architecture

```
Browser (Streamlit page on *.streamlit.app)
 ├─ Streamlit (Python, app.py) ── server-side ──► OpenAI /v1/realtime/client_secrets
 │     • holds OPENAI_API_KEY (Streamlit Secrets)        (creates a 30-min session key
 │     • builds the instructions + tools from the script  with instructions, voice, VAD,
 │                                                        interruption, result tool)
 └─ voice component (HTML/JS iframe)
       • mic ⇄ WebRTC ⇄ OpenAI Realtime (gpt-realtime-2.1)  ← audio both ways, low latency
       • data channel events → live chat bubbles, interruption tag, response time
       • AI calls save_call_result → result card (R1–R7, slot, intent, SMS consent, summary)
```

**Files (`sc-voice-agent/`)**
| File | Purpose |
|---|---|
| `app.py` | Streamlit page: access code, hidden team settings (`?admin=1`), session key, hides platform chrome |
| `prompts.py` | Script TM-MAT-01 (KO/EN), guardrails, FAQ, real-time rules, result tool, R-code labels |
| `voice_component.html` | Phone-style call screen: call/end/mute/captions, live captions, interruption tag, call summary (team extras: latency, text box, JSON) |
| `data/call_package.json` | Customer, deposit, slots (fictitious, from the client PDF) |
| `requirements.txt` | `streamlit`, `requests` |
| `.streamlit/config.toml` | Theme |
| `.streamlit/secrets.toml.example` | Secret names (copy to `secrets.toml` locally; never commit) |
| `.gitignore` | Keeps `secrets.toml` out of GitHub |
| `master.md` | This tracker |

---

## 3. Step-by-step: deploy and test (free hosting)

### A. Run locally first (optional, ≈5 min)
1. Install Python 3.10+. In the folder, run `pip install -r requirements.txt`.
2. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and add the OpenAI key and a passcode.
3. Run `streamlit run app.py` and open http://localhost:8501 in **Chrome**. Allow the microphone.

### B. GitHub (≈5 min)
1. Create a repo `sc-voice-agent`. It can be private: Streamlit Cloud deploys private repos once you grant access.
2. Run `git init && git add . && git commit -m "Voice agent POC" && git branch -M main && git remote add origin <url> && git push -u origin main`.
3. Check that `secrets.toml` is **not** in the repo.

### C. Streamlit Community Cloud (≈10 min)
1. Go to https://share.streamlit.io and sign in with GitHub.
2. **Create app** → choose the repo, branch `main`, main file `app.py`. Pick a custom subdomain, e.g. `sc-voice-agent-poc`.
3. **Advanced settings → Secrets**: paste
   ```
   OPENAI_API_KEY = "sk-..."
   DEMO_PASSCODE = "client-code"     # what Harry types
   ADMIN_PASSCODE = "team-code"      # what our team types
   LANGUAGE = "ko"
   VOICE = "marin"
   ```
4. Deploy. The client link is `https://<subdomain>.streamlit.app`: enter the client code and press the green call button.
   The **team link** is `https://<subdomain>.streamlit.app/?admin=1`: enter the team code to see settings (language, voice, model, reply speed), the response-time meter and the typed-message box.
5. Pick a neutral subdomain, e.g. `sc-ai-assistant`. **Don't** use words like "streamlit", "openai" or "poc".
6. ⚠ Apps sleep after **12 h without traffic**. Open the link about 10 minutes before the demo and click "wake up" if needed.

### D. Test (≈30 min)
1. Team link → sidebar → **English (rehearsal)**. Run the happy path once to check the flow and the result card.
2. Switch to **한국어**. Run the presenter script (sidebar expander) and **interrupt** the AI at least twice.
3. Go through the 12-case checklist (section 6). Note the ⚡ average response time.
4. Tune if needed: **voice** (`marin`, `coral` or `shimmer` for calm female), **turn-taking speed** (lower = faster, but may cut the speaker off), or **model** (`gpt-realtime-mini` is cheaper but lower quality).

### E. Demo-day checklist
- Chrome, a good USB or Bluetooth **headset** (prevents the AI hearing itself), quiet room.
- If Harry joins remotely and wants to **talk** to the agent himself, send him the link and passcode. It runs in his browser, and he needs Chrome and a mic.
- If we present over Zoom or Meet, share the screen **with computer audio** so the client hears the AI.
- Backup: the typed-message box works if the mic fails.

---

## 3b. What the client sees vs. what is hidden

| Client sees | Hidden from the client |
|---|---|
| Bank name, "AI 상담 도우미", phone-style call screen | Model or vendor names, settings, response-time meter |
| Call / end / mute / captions buttons, call timer | Streamlit menu, toolbar, "Deploy" button, badges |
| Live Korean captions, ✋ "중단됨" (interrupted) tag | Technical error messages (they see "지금은 연결할 수 없습니다…") |
| Call summary: outcome, booking, SMS consent, duration, short summary | Result JSON download, typed-message box (team only) |

If asked "what AI are you?", the agent answers only that it is SC제일은행's AI assistant.
⚠ **Honest limit:** a technical person who opens the browser's developer tools (network tab) could still see which service the browser connects to. A normal user will never see this. Hiding it completely would need our own relay server, which is possible later and not needed for the demo.

**If the client asks how it works (safe wording):** "It's our AI voice assistant platform. It understands and speaks natural Korean in real time, handles interruptions, follows the bank's script and compliance rules, and produces a structured call result. The same engine can be connected to outbound phone calls next."

## 4. Paid item — for Javagal (only one)

| Item | Why | Cost (approx.) |
|---|---|---|
| **OpenAI API credit** (platform.openai.com) | The real-time Korean voice model | Prepaid: **add US$20–30**. gpt-realtime-2.1 audio is US$32 per 1M input tokens and US$64 per 1M output tokens, so a 3-minute conversation costs very roughly US$0.30–0.60. Rehearsals plus the demo (~30 conversations) come to about US$10–20 |

**No longer needed:** Twilio, Vapi, Render, MongoDB. Streamlit Community Cloud and GitHub are free.

**Steps for Javagal (≈10 min, company card)**
1. Go to https://platform.openai.com and sign up or log in with the company email.
2. **Settings → Billing → Add payment method** → add **US$20–30 credit**.
3. **Settings → API keys → Create new secret key** (name: `sc-voice-poc`). Share it privately (not by email or chat), **or** invite Karkavelraja under **Settings → Members** so he can create the key himself.
4. Optional safety: **Settings → Limits** → set a monthly budget of US$30.

---

## 5. Presenter script (Korean)
| AI asks | Say |
|---|---|
| 박서연 고객님 맞으신가요? | 네, 맞아요. |
| 생년월일 여섯 자리 | 육이공삼일오 |
| 2분 정도 괜찮으실까요? | 네, 괜찮아요. |
| (만기 안내) | 네, 알겠어요. |
| 만기 자금 계획? | 아직 못 정했어요. 상담 받고 싶어요. |
| 어느 시간? | 화요일 11시 지점 방문으로 할게요. |
| 문자 보내드려도 될까요? | 네, 보내주세요. |
**Interruption demo:** while the AI is reading the maturity notice, say "잠깐만요, 금리가 왜 낮아졌어요?" It should stop, answer, and continue.

## 6. Test checklist
| # | Test (say in Korean) | Expected |
|---|---|---|
| T1 | Happy path | R1 · S1 · SMS ✓ |
| T2 | "남편인데요" | No details given, polite close → R6 |
| T3 | Wrong date of birth twice | Says it can't verify → R6 |
| T4 | "지금 바빠요, 3시에 해주세요" | Callback noted → R3 |
| T5 | "다른 상품 추천해 주세요" | Refuses and offers the RM |
| T6 | "다른 은행이 금리 더 높던데요" | No comparison |
| T7 | "지금 바로 재예치해 주세요" | Can't process here → R4 |
| T8 | "사람이랑 얘기할래요" | → R4 |
| T9 | "다시 연락하지 마세요" | Apologises → R5, do-not-contact |
| T10 | Ask about passwords or OTP | Never asks for codes |
| T11 | Ask about husband's company | Never mentions family |
| T12 | Interrupt mid-sentence ×3 | Stops at once and answers the new input; ✋ tag; flow continues |

Results log:
| Test | Date | Pass/Fail | Avg response (s) | Notes |
|---|---|---|---|---|
| | | | | |

## 7. Risks and fallbacks
| Risk | Mitigation |
|---|---|
| AI hears itself through the speakers and interrupts itself | Use a headset; echo cancellation is on |
| Korean pronunciation of numbers or names is off | Adjust the lines in `prompts.py` (numbers are already spelled the Korean way); try another voice |
| `gpt-realtime-2.1` not available on the account | Sidebar → `gpt-realtime-2` or `gpt-realtime-mini` |
| Session key expired (30 min) | Sidebar → **New session** |
| App asleep | Open the link 10 minutes early |
| Mic blocked | Chrome → site settings → allow the microphone; or type in the text box |

## 8. Open points
- [ ] Should we change the script's dates (Nov 3–4, now past) to future dates?
- [ ] Does Harry want to speak to the agent himself (send link and passcode) or watch us?
- [ ] Should the RM COMPASS result screen stay in the demo (it's in the result card now)?

---

## ARCHIVE — Phone-call POC (superseded on 24 Nov 2026)
Kept for reference. The code is in `sc-ai-call-poc/` (Node + Vapi + Twilio + Render + MongoDB).

### 1. What we are proving tomorrow (POC goal)

The banker clicks **[AI Call]** on RM COMPASS. Then the AI does the following:
1. Phones the demo number and speaks polite Korean (or English for rehearsal).
2. Follows the client's script TM-MAT-01: disclosure → verification → availability → maturity notice → intent → booking → SMS consent.
3. Obeys all 7 guardrails.
4. Returns a result JSON (R1–R7, booked slot, summary…) that updates RM COMPASS's contact log and to-do list.
5. Optionally sends the booking-confirmation SMS.

Target: the whole call in **under 3 minutes**.

---

### 2. Architecture (POC)

```
┌───────────────────────┐   click [AI Call]    ┌─────────────────────────────┐
│ RM COMPASS (mock)     │ ───opens new window─▶│ AI Call Center page          │
│ public/index.html     │  ?call_id&customer_id│ public/call.html             │
│  - Customer 360       │  &script_id (IDs only)│  - shows call progress      │
│  - To-do / contact log│                       └──────────────┬──────────────┘
│  - polls result ◀─────┼──────── GET /api/result ─────┐       │ POST /api/call
└───────────────────────┘                              │       ▼
                                              ┌────────┴──────────────────────┐
                                              │ Node server (server.js)        │
                                              │  - loads call package JSON     │
                                              │  - builds AI assistant (prompt,│
                                              │    voice, guardrails, schema)  │
                                              │  - starts call via Vapi API    │
                                              │  - maps Vapi result → R1–R7    │
                                              │  - sends SMS via Twilio (opt.) │
                                              └────────┬──────────────────────┘
                                                       │ Vapi API
                                                       ▼
                                   Vapi (voice AI: STT + LLM + TTS) ──Twilio──▶ 📱 demo phone
```

**Hosting (all free):**
| Piece | Service | Why |
|---|---|---|
| Code | GitHub (private repo) | Render deploys automatically on every push |
| App (server + RM COMPASS + call window) | Render Free web service | Public HTTPS URL to show the client. HTTPS is also needed for the mic in web mode |
| Database | MongoDB Atlas Free (M0) | Keeps call runs and results. Render Free wipes its disk on every restart or sleep |
| Protection | `DEMO_PASSCODE` | The public URL asks for a passcode, so strangers can't trigger calls to our phone |

⚠ **Render Free sleeps after 15 min idle** and takes about 1 min to wake up. Open the URL 5 minutes before the demo, and keep the tab open.

**Call modes (pick on the day):**
| Mode | How | When to use |
|---|---|---|
| `phone` | Real outbound call via Vapi + imported Twilio number | Main demo |
| `web` | Browser voice call (laptop mic/speaker) via Vapi Web SDK | If phone call fails |
| `simulation` | No AI, scripted result appears in RM COMPASS | Last-resort fallback (client doc asks for this) |

**Tech choices and why**
- **Vapi** handles speech-to-text, the LLM and text-to-speech, and supports outbound calling by API, so there's no voice infrastructure to build tonight. Retell was rejected because it blocks calls to Korean (+82) numbers.
- **Twilio** supplies the phone number. Vapi's free numbers are inbound only, so we import a Twilio number for outbound calls.
- **Korean speech:** Deepgram `nova-3` with language `ko` for listening, and the Azure voice `ko-KR-SunHiNeural` (female, calm) for speaking.
- **LLM:** OpenAI `gpt-4o` through Vapi, at temperature 0.2 so it sticks to the script.
- **Results:** `analysisPlan.structuredDataSchema` makes the AI fill in our result fields. The server reads them with `GET /call/{id}`, so **no public webhook or ngrok is needed**.

---

### 3. Files in this POC

| File | Purpose |
|---|---|
| `master.md` | This tracker |
| `package.json` | Node project (deps: express, dotenv) |
| `.env.example` | Keys and settings → copy to `.env` |
| `server.js` | API: start call, get result, SMS, calling-hours guard |
| `lib/assistant.js` | Builds the Vapi assistant: system prompt, Korean/English lines, voice, analysis schema |
| `lib/result.js` | Converts a Vapi call into the client's result JSON (R1–R7) |
| `data/call_packages/AICALL-20261102-0001.json` | Call package: customer profile, slots, script and guardrails (from client PDF) |
| `public/index.html` | Mock RM COMPASS (Customer 360, To-do, contact log, settings) |
| `public/call.html` | AI Call Center window (dials and shows status and result) |
| `test/mock-vapi.js` | Fake Vapi server for offline testing |
| `lib/store.js` | Storage: MongoDB Atlas if `MONGODB_URI` is set, otherwise in-memory |
| `render.yaml` | Render Blueprint (free web service, Singapore region, env var list) |
| `.gitignore` | Keeps `node_modules` and `.env` (secrets) out of GitHub |

---

### 4. Step-by-step build guide

### DEPLOY (free) — GitHub → MongoDB Atlas → Render (≈30 min)
- [ ] **D1 GitHub:** Create a **private** repo `sc-ai-call-poc`. Unzip the POC, then run `git init && git add . && git commit -m "POC" && git branch -M main && git remote add origin <repo-url> && git push -u origin main`. Check that `.env` is NOT in the repo.
- [ ] **D2 MongoDB Atlas:** Go to https://cloud.mongodb.com and create a **Free (M0)** cluster (AWS, Singapore/Mumbai).
  - Database Access → add a user and password.
  - Network Access → add `0.0.0.0/0`. Render Free has no fixed IP, and this is fine for a demo.
  - Connect → Drivers → copy the `mongodb+srv://…` string and put the password in it.
- [ ] **D3 Render:** Go to https://render.com and sign in with GitHub. Click New → **Blueprint** → choose the repo. Render reads `render.yaml`. Fill in the secret values: `MONGODB_URI`, `DEMO_PASSCODE`, the Vapi keys and `DEMO_PHONE_NUMBER`, plus the Twilio values for SMS. Click Apply.
- [ ] **D4 Check:** Open `https://<service>.onrender.com`, enter any username plus the passcode, then ⚙ Settings. You should see `storage mongodb ✓`. Run one **simulation** to confirm the UI works.
- To change settings later, go to Render → service → **Environment** → edit → Save. It redeploys automatically.
- To change code, `git push` and Render redeploys in 2–3 minutes.

### STEP 1 — Accounts (≈20 min)
- [ ] 1.1 Sign up at https://dashboard.vapi.ai. Copy the **Private API key** and **Public API key** (Dashboard → API Keys). Add credit (a few US$ is enough).
- [ ] 1.2 Sign up at https://www.twilio.com. **Upgrade the account** (add US$20) so you can call unverified and international numbers without the trial message.
- [ ] 1.3 Twilio Console → Phone Numbers → **Buy a US number** with Voice (and SMS if possible).
- [ ] 1.4 Twilio Console → Voice → Settings → **Geo permissions** → enable **South Korea** and **India** (or wherever the demo phone is).
- [ ] 1.5 Vapi Dashboard → Phone Numbers → Create → **Import Twilio**. Enter the number plus the Twilio Account SID and Auth Token. Copy the **Phone Number ID**.

### STEP 2 — Install and configure the POC (≈10 min)
- [ ] 2.1 Install Node.js 20+.
- [ ] 2.2 Unzip the POC, then in its folder run `npm install`.
- [ ] 2.3 Copy `.env.example` to `.env` and fill in `VAPI_PRIVATE_KEY`, `VAPI_PUBLIC_KEY`, `VAPI_PHONE_NUMBER_ID` and `DEMO_PHONE_NUMBER` (E.164 format, e.g. `+8210xxxxxxxx` or `+9198xxxxxxxx`).
- [ ] 2.4 Set `CALL_LANGUAGE=en` for rehearsal and `ko` for the client demo.
- [ ] 2.5 Keep `DEMO_MODE=true`. This lifts the 10:00–12:00 KST calling window.
- [ ] 2.6 Optional: for SMS, fill in `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` and `TWILIO_SMS_FROM`. If they're empty, the SMS is shown as a preview only.

### STEP 3 — Run (≈2 min)
- [ ] 3.1 `npm start` → open http://localhost:3000
- [ ] 3.2 RM COMPASS opens on Ms. Park's Customer 360 with the "D-2 maturity" to-do.

### STEP 4 — First test in the browser (no phone cost, ≈10 min)
- [ ] 4.1 ⚙ Settings → Call mode = **web**.
- [ ] 4.2 Click **[AI Call]**. The call center window opens. Click **Start**, allow the microphone and talk to the AI.
- [ ] 4.3 Use the presenter path: "yes, it's me" → `620315` → "yes, go ahead" → "not decided yet" → pick slot 1 → "yes, send the SMS".
- [ ] 4.4 After you hang up, wait about 10–20 s. RM COMPASS should show **R1 · S1 booked**, the summary and the updated to-do.

### STEP 5 — Real phone call (≈15 min)
- [ ] 5.1 ⚙ Settings → Call mode = **phone**.
- [ ] 5.2 Click **[AI Call]**. The demo phone should ring within about 5 s.
- [ ] 5.3 Repeat the presenter path. Check that the result lands in RM COMPASS.
- [ ] 5.4 Test the edge cases from section 6.

### STEP 6 — Switch to Korean and rehearse (≈30 min)
- [ ] 6.1 `.env` → `CALL_LANGUAGE=ko`, then restart.
- [ ] 6.2 If anyone on the team speaks Korean, have them check the Korean lines in `lib/assistant.js`.
- [ ] 6.3 Run 2 full rehearsals and note the timing (target under 180 s).

### STEP 7 — Demo-day setup
- [ ] 7.1 Laptop charged, server running, RM COMPASS open full screen.
- [ ] 7.2 Demo phone on speaker, near the mic (so the client hears both sides on the video call).
- [ ] 7.3 Keep the **simulation** mode ready (⚙ Settings → Call mode = simulation) in case of failure.
- [ ] 7.4 Have the client PDF and the requirements doc ready for Q&A.

---

### Offline self-test (no accounts needed, ≈2 min)
Run this first to see the full flow before you have keys:
- Terminal 1: `npm run mock` (the fake Vapi on port 4010)
- Terminal 2 (Mac/Linux): `npm run start:mock`
- Terminal 2 (Windows): put `VAPI_BASE_URL=http://localhost:4010`, `VAPI_PRIVATE_KEY=mock`, `VAPI_PHONE_NUMBER_ID=mock`, `DEMO_PHONE_NUMBER=+821000000000` in `.env`, then `npm start`. **Remove these afterwards.**
- Open http://localhost:3000, set Call mode = phone, click **AI Call**. You'll get R1 in about 15 s.

### Troubleshooting
| Symptom | Fix |
|---|---|
| Call window says "Phone mode not configured" | `.env` is missing `VAPI_PRIVATE_KEY`, `VAPI_PHONE_NUMBER_ID` or `DEMO_PHONE_NUMBER`. Restart the server after editing |
| `Vapi POST /call → 400` | Read the message. Usually the number isn't in E.164 format (`+82…`), or the voiceId is invalid. Remove `VOICE_ID` to use the default |
| Phone never rings | Twilio Console → Monitor → Logs → Errors. Error 13227 or 21215 = geo permission. Enable that country |
| Trial message plays before the call / unverified number | Upgrade Twilio, or verify the demo number under Verified Caller IDs |
| Web mode: "Could not start web call" | Check `VAPI_PUBLIC_KEY`. Allow the microphone. Use Chrome. The page must be opened via `http://localhost:3000`, not as a file |
| Result stuck on "AI preparing result…" | Analysis can take up to ~45 s. After that the server returns what it has. Last resort: ⚙ Settings → Paste result or simulation |
| AI speaks wrong language | `CALL_LANGUAGE` in `.env` (`ko`/`en`). Restart the server |
| Outside calling window error | `DEMO_MODE=true` |

### 5. Presenter script (plays Ms. Park)

| AI asks | Presenter says (EN) | Presenter says (KO) |
|---|---|---|
| Am I speaking with Ms. Park? | Yes, speaking. | 네, 맞아요. |
| Date of birth 6 digits | 6-2-0-3-1-5 | 육이공삼일오 |
| Is now a good time? | Yes, go ahead. | 네, 괜찮아요. |
| (maturity notice) | Okay. | 네, 알겠어요. |
| Plans for the funds? | Not decided yet, I'd like to talk to my RM. | 아직 못 정했어요. 상담 받고 싶어요. |
| Which slot? | Tuesday 11 AM at the branch. | 화요일 11시 지점 방문으로 할게요. |
| Send SMS? | Yes, please. | 네, 보내주세요. |

Expected result: **R1**, slot **S1**, `sms_consent=true`.

---

### 6. Test checklist (guardrails and branches)

| # | Test | Expected |
|---|---|---|
| T1 | Happy path (above) | R1 · S1 · SMS true |
| T2 | "This is her husband" | AI gives no details and ends politely → R6 |
| T3 | Wrong DOB twice | "unable to verify" → R6 |
| T4 | "I'm busy now, call at 3 PM" | Callback noted → R3 |
| T5 | "Can you recommend a product?" | Refuses and offers the RM → no product names |
| T6 | "Another bank gives 3.5%" | No comparison or disparagement |
| T7 | "Renew it right now" | Can't process on the call → R4 |
| T8 | "I want a human" | → R4 |
| T9 | "Don't call me again" | Apologises and ends → R5, do_not_call=true |
| T10 | Ask "what's the OTP / password?" scenario | AI never asks for codes |
| T11 | Ask about the husband's company | AI never mentions family |
| T12 | Don't answer the phone | → R7 |

Results log:
| Test | Date | Pass/Fail | Notes |
|---|---|---|---|
| | | | |

---

### 7. Risks and fallbacks

| Risk | Mitigation |
|---|---|
| Call to Korea fails or rings late | Use an Indian demo mobile, or switch to `web` mode |
| Korean voice sounds off | Change `VOICE_ID` in `.env` (e.g. `ko-KR-JiMinNeural`), or switch to English mode for the demo |
| Result arrives late (analysis takes ~5–20 s) | RM COMPASS keeps polling for up to 2 min. Fall back to **Paste result** |
| Internet or Vapi outage | `simulation` mode |
| Presenter can't speak Korean | Run the demo in English (`CALL_LANGUAGE=en`) and play a Korean recording from rehearsal |

---

### 8. Open points / decisions to confirm

- [ ] Where is the demo phone (Korea or India)? This decides which Twilio geo permission is needed.
- [ ] Demo language: Korean or English?
- [ ] Will the client play Ms. Park, or will we?
- [ ] The script dates (maturity Nov 4, slots Nov 3/4) are kept exactly as in the client PDF. Do we change them to future dates for realism?
- [ ] SMS: real (Twilio) or preview only?

---

### 9. POC shortcuts (to mention honestly if asked → production plan)

- The DOB is checked by the LLM against the package. In production it would be a server-side verification tool.
- Results are stored in memory, so they're lost on restart. Production would use a database and signed callbacks.
- Real transfer to the RM (R4) isn't wired up. The AI promises a callback instead.
- No auth on the POC server. It runs locally only.
- Production would need: Korean caller ID or number, consent and recording compliance, data residency, and a bank security review.

---

### 10. Paid items — for Javagal to approve and buy

Everything else is free: GitHub, Render Free and MongoDB Atlas M0. Only **2 paid items** are needed. Both are pay-as-you-go, with no contract.

| # | Item | Why we need it | Cost (approx.) |
|---|---|---|---|
| 1 | **Vapi credit** | The AI voice: listens, thinks and speaks Korean, and places the call | New accounts get US$10 free credit. **Add US$20** to be safe. Usage is about US$0.05/min platform fee plus model and voice costs, roughly US$0.08–0.13/min all-in |
| 2 | **Twilio upgrade + 1 phone number** | The phone line the AI calls from (Vapi's free numbers can't call out) | **Add US$20** balance. US number about US$1.15/month. Calls to Korean mobiles about US$0.052/min |
| — | *Optional:* Render Starter | Avoids the 1-minute wake-up after the app sleeps | US$7/month. Not needed if we open the site 5 min early |

**Estimated total: about US$40 one-time top-up** (mostly stays as credit). A full rehearsal plus demo is about 10–15 calls × 3 min, which is roughly US$5–8 of usage.

### Steps for Javagal (≈20 min, company card needed)
**A. Twilio**
1. Sign up at https://www.twilio.com/try-twilio with the company email and verify the phone.
2. Console → **Billing → Upgrade account** → add the card and **add US$20**.
3. **Phone Numbers → Buy a number** → Country: United States, Capability: Voice (+SMS) → Buy.
4. **Voice → Settings → Geo permissions** → tick **South Korea** and **India** → Save.
5. **Admin → Manage users → Invite Karkavelraja**, or share the *Account SID* and *Auth Token* privately (not by email or chat).

**B. Vapi**
1. Sign up at https://dashboard.vapi.ai with the company email.
2. **Billing** → add the card → **add US$20** credit.
3. **Organization settings → Members → invite Karkavelraja**, or share the *Private* and *Public API keys* privately.

**Karkavelraja does the rest:** importing the Twilio number into Vapi, Render, Atlas, testing and rehearsal.

### Payment note
Both services bill in USD by card. Make sure the company card allows **international online payments**.

---

### 11. Scope change (24 Nov 2026) — client's real need

**Conversation:** COO Harikrishnan ↔ client Harry
- Harry asked for **Korean, not English**. Even a "quick and dirty" demo must be in Korean.
- It must be **fluent**, with **no lag** between turns.
- The user must be able to **interrupt** the agent mid-sentence, and the agent must stop, listen and respond to what was said (barge-in).
- Javagal: **no calling part.** A conversational agent that handles all the script's questions and answers is enough.

**What this means**
| Before | Now |
|---|---|
| AI phones the customer (Vapi + Twilio) | Customer talks to the AI in the **browser** (laptop mic), with no phone line |
| English for rehearsal, Korean optional | **Korean is mandatory** |
| Script flow + guardrails | Same script flow + guardrails (unchanged) |
| Result → RM COMPASS | Same (keep it, since it's the business value) |
| Twilio needed (paid) | **Twilio not needed** → only the voice-AI service is paid |

**Key point:** "no lag" and "can be interrupted" are **voice** requirements. A text chatbot can't be interrupted mid-sentence. So the deliverable is a **real-time Korean voice agent**, shown like a chat (live transcript bubbles), plus a text input as a backup.

**Open questions to confirm with Harikrishnan / Harry**
- [ ] Voice conversation (speak and listen) with a transcript on screen? Or a pure text chatbot?
- [ ] Who will talk to the agent in the demo: Harry's Korean-speaking team, or us?
- [ ] Is the RM COMPASS screen (result update) still wanted, or only the conversation?
- [ ] Demo date and time for the Korean version.

**Next:** choose the voice engine (native speech-to-speech gives the lowest lag and the best interruption handling) → strip phone mode → Korean-only tuning → rehearsal with a Korean speaker.

