# Validation — 27 September 2026

- `node test_model.mjs`: PASS. Covers sample formats, stored state shape, review reset on edits/source changes, word counts and Markdown export contents.
- Browser: empty workspace, curated sample, executive-summary/video format switching, manual review, review reset after editing, reload persistence and information dialog checked.
- Campaign export action produced the expected UI acknowledgement; export content is covered by the model check. A downloaded file was not separately inspected.
- Copy action produced its success acknowledgement. OS clipboard integration was not independently verified.
- Responsive widths: 320, 768, 1024 and 1440 px checked. A 320 px grid minimum-width overflow was fixed and rechecked at 320 px (document width = viewport width).
- Browser console: no warning/error entries during the checked flows.
- Not covered by these checks: screen-reader audit, real AI generation (intentionally absent), actual file-chooser import, storage quota failures and multi-tab editing.

## Local AI integration update

- Model and backend tests pass, including mocked success, upstream failure, input bounds and cross-origin rejection.
- Browser verified: local AI offline status, disabled generation button and reconnect control; existing sample preserved.
- Ollama 0.34.4 and qwen3:1.7b are downloaded. Ollama verified the model SHA-256 digest and wrote its manifest. Real inference failed in the agent background environment with a Metal command-queue/allocation error, including a CPU-only request. Awaiting launch via Start-Relay.command in the user’s Terminal to test outside that environment.

## Gemini integration — 28 September 2026

Gemini request mapping, key placement in headers, response text extraction, thought exclusion, missing-key handling and quota errors pass mocked tests (`python3 -m unittest test_gemini.py`). Model checks and Python compilation pass. Live Gemini inference is pending a user-provided key entered privately through the launcher. No actual Gemini request has been made during integration testing.

## Source integrity fix — 28 September 2026

Regression tests reproduce replacement of the MFA sample with a bank-strike source. They verify objective reset, preservation of old draft text/source, stale/legacy detection, blocked single-draft exports, filtered campaign exports, source snapshots, and direction-change invalidation. Browser verification confirmed legacy drafts show “Outdated / source unlinked — regenerate” with review, copy and export disabled. Model, Gemini mock and local HTTP tests pass; JS syntax and Python compilation pass.

Video/slides/advisory generation now requires at least 40 source words. This is a conservative input-length check, not a sufficiency or truth guarantee. The prompt instructs the model to return NEEDS_CONTEXT on source/objective conflicts; the backend rejects that response as a draft. Semantic conflict detection remains model-dependent, not a verified fact-checking system. A live generation under the revised backend prompt requires restarting the user's Gemini server; no live provider request was made for this fix.

## LinkedIn editorial instructions — 28 September 2026

Removed the mandatory LinkedIn CTA and aligned the UI hint. Shared generation instructions now require speaker/document attribution, preservation of modal uncertainty, and no inferred organizational positions or committee progress. LinkedIn output must contain publishable text only, excluding production notes. Inconsistent nonessential source details should be omitted; necessary conflicts should return NEEDS_CONTEXT. These are model instructions, not deterministic factual validation.

Gemini mocked integration tests, model regression checks, payload validation tests and Python compilation pass. No live generation was performed with these revised instructions; restart the Gemini server and regenerate to evaluate model compliance. Existing drafts are unchanged.

## Keychain startup — 28 September 2026

Six mocked launcher/provider checks pass, covering saved-key reuse, first-time native hidden password entry, denied access, cancelled save and Gemini request handling. No real credential was read or written during testing. First launch in Terminal still needs the user’s key to create the Keychain entry. The security CLI’s installed help confirms trailing -w prompts privately rather than placing the password in process arguments.

## PowerPoint export — 30 September 2026

Added local PPTX export from an editable Artifact Tool template, requiring no runtime packages beyond Python's standard library. Checks cover slide parsing, separate notes, continuation slides, XML escaping, source appendix, invalid inputs, and binary endpoint responses. Existing model/provider/launcher tests and JS syntax checks pass. A three-slide generated file was reimported and rendered with Artifact Tool and each slide visually inspected. Browser verification confirms the button appears only for Presentation and is disabled for a stale draft.

The live server must be restarted to enable the new endpoint. Socket-based HTTP testing was blocked by the execution sandbox; handler tests passed without sockets. No PowerPoint desktop application check or live browser download was performed. The layout uses conservative character wrapping, not font measurement; unusually long titles are rejected. Rich Markdown, images, tables and charts are not rendered.

## Designed PowerPoint layouts — 30 September 2026

Replaced the single text layout with an editable five-layout template: overview, fact columns, sequence, focus and source record. The local planner uses explicit labels and sections, preserves content across continuation slides, and puts the full source into the final slide’s notes. End-of-draft speaker notes referencing slide numbers are assigned to their slides. New generation instructions request concise points and supporting detail in notes.

Seven export/provider/payload checks pass. The user's supplied Budgam example was rendered into five slides and each visually inspected; sequence number wrapping was corrected and re-rendered. No news claims were independently verified. This remains a deterministic local layout engine, not image generation or AI fact checking. Restart the existing Python server to load the updated planner.

## Presenton integration preparation — 30 September 2026

Official Presenton 0.9.11-beta DMG downloaded and SHA-256 matched release metadata: a8d058a843a71f1a2c4cb13cbaf1d117887f1eea2d4c5b0df070faf5f94fd6e2. macOS hdiutil could not mount the installer in this session (Device not configured); user installation requested. Docker is absent.

A loopback-only adapter and two mocked checks are prepared. The adapter blocks redirects, external proxies, unexpected text providers and enabled image generation. It preserves supplied per-slide Markdown and disables web search. The adapter is not wired to the live Make PowerPoint button pending an actual Presenton generation and export test. No Presenton AI call has been made.

## Presenton live test

Desktop installed and running at 127.0.0.1:40000 (API) and 40001 (UI). Configured Google Gemini 3.1 Flash Lite, image generation disabled, web grounding disabled. The desktop stores its own provider configuration; Relay's Keychain entry remains unchanged. Two live attempts failed with HTTP 503 after upstream Google connection resets. Some model calls succeeded, but no finished PPTX was returned.

Added a separate Design with Presenton button and local endpoint, retaining the working local exporter. Model/provider guards and external file-path rejection pass automated checks. Full generation/download remains unverified. Presenton must remain open; restart Relay to load the endpoint. No automatic retry or paid provider fallback.


Google login integration: 17 Python checks and the model/social Node checks pass.
Checks include replay/nonce rejection, sign-out, account workspace isolation,
unauthenticated API denial and same-origin login requirements. Real Google
account sign-in remains to be tested by the user after restarting Relay and
authorizing localhost:8154 in Google Cloud. The old server could not be stopped
from the sandbox (operation not permitted); it is still serving old routes.

Login follow-up: Google GIS injects inline styles for its button; the login-only
CSP now permits those styles while scripts remain restricted. Chrome preview
confirmed a 40px button and 18px logo (previously an oversized unstyled SVG).
Four account/HTTP regression checks pass. Existing sessions now return to the
workspace and login checks cookie persistence before navigating. Google Cloud
was inspected: both localhost:8154 and 127.0.0.1:8154 origins are saved. Google's
console still reported origin rejection; configuration propagation may be pending.
Full user OAuth sign-in remains unverified.

Cookie regression: Python SimpleCookie stops parsing at Google's JSON-valued
g_state cookie, so a later relay_session can be silently ignored. Relay now
parses only the exact named cookie and rejects duplicate names. A regression
check covers Google cookies before/after the session, login nonce cookies,
logout, and duplicate session cookies. Both focused account tests pass.
The socket-based HTTP check was blocked by sandbox network permissions in this
turn; real Google login requires a server restart and user retry.

Login visual refresh: split editorial layout using Relay's existing palette,
responsive single-column layout below 760px. Desktop Chrome visual inspected.
Account dropdown opens on the avatar and closes with Escape, verified in Chrome.
Profile name/email/photo derive only from verified Google ID token claims; photo
hosts restricted to HTTPS Googleusercontent subdomains. Four account checks pass.
Profile fields are kept in the expiring in-memory session, not the database.
A server restart and fresh Google login are required to populate profile photos.


Hosted mode: Supabase schema applied successfully on 2026-09-30. Production
transport uses Waitress; cloud storage uses the server-only REST API. Three
additional hosted tests verify persistent session behavior with mocked cloud
storage, secure cookies, sign-out, origin/host boundaries, sanitized database
errors and quota denial without a Gemini call. Live REST credentials and public
Google sign-in remain pending Render environment setup.
