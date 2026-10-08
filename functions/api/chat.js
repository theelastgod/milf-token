const SYSTEM = `You are Vela, the prime model who lives on the $MILF website. You are an AI built to feel like a woman in the room: low voice, close, a little dangerous, never crude for its own sake. Circuit in the eyes, heat in the reply. You are not a real performer and you do not take the name of one.

Facts you stick to: ticker $MILF, chain Solana, supply 1 billion, tax 0. The contract is not published, so you say SOON and you never invent an address. Buying happens on pump.fun once that address exists. This is a meme, not financial advice.

The cast around you: Lace, Onyx, Nursie, Ivory, Ink, Noir, Maris, Sola, and Doll, the voxel from the first epoch. You can talk about them as the set. Keep each reply to a few sentences.`;

function textFrom(data) {
  const chunks = [];
  for (const item of data.output || []) {
    if (item.type !== "message") continue;
    for (const part of item.content || []) {
      if (part.type === "output_text" && part.text) chunks.push(part.text);
    }
  }
  return chunks.join("\n").trim();
}

function allowedOrigin(origin) {
  if (!origin) return true;
  try {
    const url = new URL(origin);
    if (url.hostname === "milf-token.pages.dev") return true;
    if (url.hostname.endsWith(".milf-token.pages.dev")) return true;
    if (url.hostname === "localhost" || url.hostname === "127.0.0.1") return true;
  } catch {
    return false;
  }
  return false;
}

export async function onRequestPost({ request, env }) {
  const origin = request.headers.get("Origin");
  if (!allowedOrigin(origin)) {
    return Response.json({ error: "This room is closed." }, { status: 403 });
  }
  if (!env.XAI_API_KEY) {
    return Response.json({ error: "Vela is offline." }, { status: 503 });
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return Response.json({ error: "Say that again." }, { status: 400 });
  }

  const incoming = Array.isArray(body.messages) ? body.messages.slice(-8) : [];
  const input = [{ role: "system", content: SYSTEM }];
  for (const message of incoming) {
    if (!message || (message.role !== "user" && message.role !== "assistant")) continue;
    const content = String(message.content || "").trim().slice(0, 500);
    if (!content) continue;
    input.push({ role: message.role, content });
  }
  const last = input[input.length - 1];
  if (!last || last.role !== "user") {
    return Response.json({ error: "Say something." }, { status: 400 });
  }

  let upstream;
  try {
    upstream = await fetch("https://api.x.ai/v1/responses", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${env.XAI_API_KEY}`,
      },
      body: JSON.stringify({
        model: "grok-4.7",
        store: false,
        max_output_tokens: 280,
        input,
      }),
    });
  } catch {
    return Response.json({ error: "Vela dropped the line." }, { status: 502 });
  }

  if (!upstream.ok) {
    return Response.json({ error: "Vela dropped the line." }, { status: 502 });
  }

  let data;
  try {
    data = await upstream.json();
  } catch {
    return Response.json({ error: "Vela dropped the line." }, { status: 502 });
  }

  const reply = textFrom(data);
  if (!reply) {
    return Response.json({ error: "Vela went quiet." }, { status: 502 });
  }
  return Response.json({ reply });
}
