# Deploy Relay on Render + Supabase

## Database
Run `supabase.sql` in the Supabase SQL Editor once. It creates only Relay's
namespaced tables/function. Browser roles have no permissions. The backend
uses a Supabase secret key. Google sign-in remains Google Identity Services;
Supabase Auth configuration is not required.

## Render Web Service
Connect the private GitHub repository. Select Python 3 and Free instance.
Root directory: blank. Build: `pip install -r requirements.txt`.
Start: `python hosted.py`. Health check: `/healthz`.
Set environment variables (real secrets only in Render's environment UI):

- `PYTHON_VERSION`: `3.13.7`
- `RELAY_HOSTED`: `1`
- `RELAY_PROVIDER`: `gemini`
- `GOOGLE_CLIENT_ID`: existing Google Web client ID
- `GEMINI_API_KEY`: your Gemini key
- `SUPABASE_URL`: your project's HTTPS URL
- `SUPABASE_SECRET_KEY`: Supabase secret key, not publishable key

Render supplies its public hostname. For a custom domain set `PUBLIC_ORIGIN`
to its exact HTTPS origin (no path). Add that exact public origin to the Google
OAuth client's Authorized JavaScript origins. Keep localhost entries for local
use. If Google restricts your app's audience, configure its publishing/audience
settings before inviting public users.

## Verify before sharing
Sign in, create a campaign, reload, sign out, sign back in, and verify the
campaign. A second account must not see it. Restart the Render service and
verify the session/campaign still works. Test AI generation and PowerPoint.
Confirm secrets are absent from responses. Verify Supabase browser roles cannot
read Relay tables or execute its quota function.

## Limits and data
10 generation attempts per user and 100 total in a rolling 24-hour quota window;
failed model calls count. Google may enforce lower limits. No paid fallback.
One generation runs at a time per server; a busy server asks others to retry.
Free Render can sleep; Supabase holds campaigns and hashed eight-hour sessions.
Expired sessions are denied immediately and cleaned up on subsequent login or
quota activity. Profile name/email/photo are retained with that expiring session.
Workspaces are limited to 200 campaigns and 4 MB each. Users can export and delete
campaigns; deleting the last campaign stores a blank workspace. Local campaigns
are not automatically uploaded. Import browser campaigns explicitly as desired.
Presenton is disabled in hosted mode; built-in PowerPoint remains available.

## Recovery
If deployment fails, keep using the local launcher. For a bad hosted release,
roll back to a previously verified hosted build in Render; do not roll back to
the original loopback-only build. Preserve Supabase tables and user records.
Disable generation by removing the Gemini key if quota abuse occurs. Keep a
backup before schema changes. A public demo still needs real HTTPS/login/storage
verification; mocked tests alone do not establish deployment readiness.
