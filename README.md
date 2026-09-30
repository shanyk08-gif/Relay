> **Deployment status:** This repository contains the working local Relay app. Public hosting is not configured yet. Supabase storage, persistent sessions, public HTTPS configuration and shared AI usage limits must be implemented before deploying on Render.

# Relay — SIH26154 local AI workspace

A local content transformation workspace for **Gen AI Platform for Automated Content Transformation**, NTRO. Built alongside NAWI Lab in a separate folder. The Python server has no external dependencies. AI requires Ollama and the local qwen3:1.7b model; no API key or paid API is used.

## Run

Double-click `Start-Relay.command` and keep its Terminal window open, or run from this folder:

```sh
python3 start_local.py
```

Open http://127.0.0.1:8154/. Do not open index.html directly: JavaScript modules need HTTP.

## Use

1. Choose **Explore sample** for a complete, explicitly fictional campaign, or **New campaign** for your own work.
2. Paste source text or import a UTF-8 `.txt` / `.md` file (150 KB, 50,000 characters maximum).
3. Set audience, tone, language, detail and objective. These preferences guide local generation.
4. Choose a format and use **Generate selected format**, or write your own draft. Generated content opens in a new campaign version, preserving the original. Write or edit any of seven output formats. Compare drafts with source excerpts, then mark them reviewed. Source/direction changes reset every review mark; draft edits reset that draft's mark.
5. Copy one draft or export a Markdown file containing one/all written drafts, source, settings and review status.

## Free local AI setup

This Mac has a project-local Ollama installation in `../../work/ollama-runtime`. The launcher uses that installation with cloud features disabled. Keep that folder alongside this project.

For a fresh installation on another Mac, install Ollama from https://ollama.com/download/mac, open it, and download the model:

```sh
ollama pull qwen3:1.7b
```

Then click **Check connection** in Relay. Ollama must be running on its default local port 11434. The model is about 1.4 GB; Ollama adds installation overhead. Downloads require internet, but this integration sends generation requests only to the local model. Runtime uses your Mac's memory, processing power and electricity. No cloud fallback is implemented.

Local generation accepts 20–12,000 source characters, one output format per request. The model is small and needs human fact checking; larger/longer-source workflows are future work. Errors leave existing drafts untouched. Generated versions retain the captured source/settings; edits made while generation runs remain in the original campaign. Output limit warnings indicate potentially incomplete drafts.

Samples are manually prepared, not generated on demand. The source pane does not verify claims automatically. Presentation, infographic and video outputs are textual plans; exports are Markdown, not PPTX, images or MP4. Hindi is passed as a model instruction, with no independent translation-quality validation.

Campaigns are saved in this browser's localStorage. They are not encrypted or synced to a server. Use one editing tab at a time; clearing browser data removes saved campaigns. Exports are readable backups, not re-importable workspace snapshots. Storage failures are shown and malformed saved data is not overwritten.

The server serves static files and forwards generation requests to local Ollama. No source text is sent to a cloud AI provider. Host and Origin checks restrict browser requests, source and output sizes are bounded, and only one generation runs at a time. Use this local prototype for demonstration; authentication, multi-user storage and deployment hardening are future work.

## Check

Requires modern Node.js (tested with the installed runtime):

```sh
node test_model.mjs
python3 -m unittest test_server.py
```

Checks sample completeness, stored record shape, review invalidation, word counts and export contents. Browser checks are recorded in VALIDATION.md.

## Files

- `index.html`, `style.css`: responsive editor
- `app.js`: UI, local persistence, import, review, export
- `model.mjs`: format definitions, state logic, sample and Markdown serialization
- `ANALYSIS.md`: official problem interpretation, proposed scope and next phases

No framework, build step or third-party dependency.

- `server.py`: local API, validation, bounded Ollama requests and static serving.
- `test_server.py`: request validation, origin rejection, mocked generation success and failure.

## Gemini (cloud alternative)

Run `python3 start_gemini.py` or double-click `Start-Gemini.command`. Stop an existing Relay server with Ctrl+C first if port 8154 is occupied. This launcher does not start Ollama.

Get a key from https://aistudio.google.com/api-keys. Confirm its project is **Free Tier**, then paste the key into the native hidden password prompt on first launch. macOS Keychain stores it as **Relay Gemini API** (account **relay**); subsequent launches reuse it without the key or FREE prompts. macOS may ask you to unlock or approve Keychain access. The key is never saved in source or browser storage. Do not paste it into chat. Closing Terminal stops the server but preserves the Keychain entry. To replace or remove it, delete that entry in Keychain Access; the next launch will run setup again.

Model: `gemini-3.1-flash-lite`, listed with a free tier as checked on 28 September 2026. Relay cannot inspect billing status or guarantee zero charges on a paid Google project. Quota failures stop generation; there is no automatic paid fallback. Source text and direction are sent to Google's Gemini API. Free-tier content may be used for product improvement; use public or synthetic material.

The connection badge confirms a key is configured, not that it is valid. Generate a sample draft to verify the key. Local Ollama remains available via `Start-Relay.command`.

## Source changes and older drafts

Changing source text clears the previous objective and resets review marks. Drafts now record their source and direction at creation. A mismatch makes the draft read-only and blocks review, copy and export. The old text is retained for reference. Campaign export includes only matching drafts and lists excluded ones. Each exported draft includes its own source snapshot.

Previously saved drafts lack this provenance and are conservatively marked unlinked; regenerate them. Editing an unlinked draft cannot establish its source history. Start a new campaign for new manually authored work. Video, slides and advisory generation require at least 40 source words; paste the full article when possible. Length checks and model instructions do not guarantee factual accuracy.

After backend changes, stop the Gemini Terminal with Ctrl+C and rerun `python3 start_gemini.py`. The launcher reuses your saved Keychain entry. Refresh Relay in every editing tab so the updated frontend is loaded. Use one editing tab at a time.

## PowerPoint download

Select Presentation, generate or write your slide draft, then click **Make PowerPoint ↓**. The local server creates an editable `.pptx` with a designed cover, fact columns, focus layouts, explicit event sequences, and speaker notes. This step uses no AI service and needs no extra installed packages. Restart the server after updating, then refresh the browser.

Use `Slide 1: Title` (or Markdown headings) followed by slide content and `Speaker notes: ...`. Keep titles under 120 characters. Long content becomes continuation slides; exports are capped at 100 slides. Layout selection follows the draft structure. A final source slide preserves the full source in its speaker notes. There are no generated images, charts or animations; export does not make another AI call. Markdown emphasis is flattened. Old/unlinked drafts remain blocked; regenerate them first.

## Presenton desktop integration

Open Presenton and use **Presentation → Design with Presenton** in Relay. Restart Relay after this update. The separate button uses the local API on port 40000, Gemini 3.1 Flash Lite, and requires image generation disabled. It sends the draft to Gemini after confirmation and uses that account's quota. Presenton stores its own provider settings, including its Gemini key. The original Make PowerPoint button stays available without AI calls.

Live test status: Google connection resets prevented a completed deck. This integration is experimental until a full generation succeeds. Errors preserve your draft and do not trigger another provider or automatic retry.


## Google sign-in
Google Identity Services client ID is saved in `google-client-id.txt`. Use
`http://localhost:8154` as an Authorized JavaScript origin in Google Cloud,
and open that address after restarting Start-Gemini.command. No client secret
is required. The launcher uses the project .venv with pinned requirements.txt.
For a fresh install: `python3 -m venv .venv` then
`.venv/bin/python -m pip install -r requirements.txt`.

This is loopback-only development: cookies are HttpOnly/SameSite with an eight-hour
session, using HTTP on localhost. Do not expose this server publicly; a hosted
version needs HTTPS and Secure cookies. Sessions expire when Relay restarts.
Google ID tokens are verified with google-auth, the configured audience and a
one-use nonce. Only Google's account identifier is retained with campaigns in
`data/accounts.sqlite3`; no Gmail/Drive access is requested. Export and delete
campaigns in the workspace. Login rate limits and sessions are in memory for
this single server.

Existing browser campaigns are preserved, with an explicit Import browser campaigns
button after sign-in. Browser storage belongs to its exact address: localhost
and 127.0.0.1 do not share it. Import from the original address/browser (that
origin must also be authorized for Google sign-in). Account campaigns stay on
this Mac, not in Google Drive. They are not synced across computers.

LinkedIn and X handoffs require a current reviewed draft and confirmation.
They copy the draft or individual X post and open the platform; publishing
remains a separate action on that platform.
