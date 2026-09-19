# Paper Trader — self-hosted version

A beginner stock-market practice game, built as one self-contained `index.html` file. This folder is set up to run on GitHub Pages or Netlify with no server and no signup for whoever plays it.

## What's in here

- `index.html` — the whole app (HTML, CSS, and JS in one file).
- `prices.json` — today's stock prices. The app reads this file on load.
- `scripts/update_prices.py` — fetches real prices and rewrites `prices.json`.
- `.github/workflows/update-prices.yml` — runs that script automatically on GitHub's servers every weekday evening, and commits the updated `prices.json` back to the repo.

## How saving and price updates work here (read this first)

This version does **not** depend on Claude at all once it's deployed — it's a plain static site. Two things work differently than the original Claude-hosted version because of that:

1. **Progress saves in the browser only.** Each buy/sell is saved with `localStorage`, in whatever browser your teen is using. That means it survives closing the tab and coming back — but it won't follow them to a different browser or device. If they play on their phone and then open the same link on a laptop, that's a separate, fresh $10,000 start. There's no login system here, so this is the trade-off for "no signup needed."
2. **Prices update once a day, automatically, via GitHub** — not via Claude. The included GitHub Action fetches real closing prices every weekday evening and commits the change, which triggers Pages/Netlify to redeploy with fresh data. You don't have to do anything for this once it's set up.

## Deploying

### Option A: GitHub Pages

1. Create a new repository on GitHub (public or private both work — Pages works either way, though a private repo needs GitHub Pro/Team/Enterprise for Pages).
2. Upload everything in this folder to that repository, preserving the folder structure (the `.github/workflows/update-prices.yml` path matters — GitHub only picks up workflows from that exact location).
   - Easiest way with no command line: on the repo's GitHub page, use "Add file → Upload files" and drag in everything (make sure the `.github` folder comes through — if GitHub's uploader drops hidden-looking folders, use `git` from a terminal instead, or GitHub Desktop).
3. Go to the repo's **Settings → Pages**. Under "Build and deployment," set Source to "Deploy from a branch," pick your main branch and `/ (root)`, and save.
4. GitHub gives you a URL like `https://yourusername.github.io/your-repo-name/` within a minute or two. That's the link to share.
5. Go to the **Actions** tab once, and confirm the "Update stock prices" workflow is listed and enabled. You can click "Run workflow" there to trigger it immediately instead of waiting for the schedule, to confirm it works.

### Option B: Netlify

1. Go to netlify.com and either:
   - **Quickest**: drag this whole folder onto Netlify Drop (app.netlify.com/drop) for an instant URL. Note: a Netlify Drop site deployed this way isn't connected to GitHub, so the price-update Action's commits won't automatically redeploy it — you'd need to re-drag the folder periodically, which defeats the point. Use this only for a quick one-time test.
   - **For real use**: push this folder to a GitHub repo first (see Option A, steps 1–2), then in Netlify choose "Add new site → Import an existing project" and connect that repo. Netlify will redeploy automatically every time the price bot commits an update.
2. Netlify gives you a URL like `https://random-name-12345.netlify.app` — you can rename it in Site settings for something friendlier.

Either option works fine; GitHub Pages is simpler if you're not going to touch Netlify's other features, Netlify is nicer if you want a custom domain or a friendlier auto-generated URL.

## If the price updates ever stop working

The script pulls from two free, no-signup data sources (Yahoo Finance's public quote endpoint, with a Stooq CSV fallback for any ticker Yahoo fails on). Free, unofficial endpoints like these occasionally change format without notice. If that happens:

- Check the **Actions** tab in the repo — a failed run shows up with a red X, and the log will show which tickers failed and why.
- Worst case, prices just freeze at their last known values (the app still works fine, just without a fresh "today" number) — nothing breaks.
- Send me the failing log and I can fix the script.

## Changing the stock list later

The 30 tickers live in two places that need to match: the `STOCKS` array near the top of the `<script>` in `index.html` (which has each stock's name and sector), and the `TICKERS` list in `scripts/update_prices.py` (which just needs the ticker symbols). Adding a stock means adding it to both.
