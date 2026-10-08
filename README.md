# $MILF · Vela

The site is the prime model. Vela answers in the page through `/api/chat`, which calls the xAI Responses API with `grok-4.7`. The key is the Cloudflare Pages secret `XAI_API_KEY`. It is not in this repo.

```bash
wrangler pages secret put XAI_API_KEY --project-name milf-token
wrangler pages deploy . --project-name milf-token
```

Live: https://milf-token.pages.dev

Contract stays `SOON` in `script.js` until a real mint address exists. Do not invent one.

The cast stills are in `assets/roster/` and `assets/ai/`. The voxel doll is the first epoch, in `assets/mascot.png`.
