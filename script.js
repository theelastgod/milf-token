const CONTRACT = "SOON";
const TWITTER = "";
const TELEGRAM = "";

const live = CONTRACT && CONTRACT !== "SOON";
const pumpUrl = live ? `https://pump.fun/coin/${CONTRACT}` : "https://pump.fun";
const chartUrl = live
  ? `https://dexscreener.com/solana/${CONTRACT}`
  : "https://dexscreener.com";
const caText = live ? CONTRACT : "SOON";

document.querySelectorAll(".js-ca").forEach((el) => {
  el.textContent = caText;
});

["buyCta", "navBuy", "dockBuy", "pumpBtn", "pumpLink"].forEach((id) => {
  const el = document.getElementById(id);
  if (el && live) el.href = pumpUrl;
});

const navChart = document.getElementById("navChart");
const dexLink = document.getElementById("dexLink");
if (navChart) navChart.href = live ? chartUrl : pumpUrl;
if (dexLink) dexLink.href = chartUrl;

const xLink = document.getElementById("xLink");
const tgLink = document.getElementById("tgLink");
if (TWITTER && xLink) xLink.href = TWITTER;
if (TELEGRAM && tgLink) tgLink.href = TELEGRAM;

async function copyCa(btn) {
  const prev = btn.innerHTML;
  try {
    await navigator.clipboard.writeText(caText);
    btn.textContent = "Copied";
  } catch {
    btn.textContent = "Copy failed";
  }
  setTimeout(() => {
    btn.innerHTML = prev;
  }, 1400);
}

["copyCa", "copyNav", "copyHero", "copyDock"].forEach((id) => {
  const el = document.getElementById(id);
  if (el) el.addEventListener("click", () => copyCa(el));
});

const navToggle = document.getElementById("navToggle");
const navLinks = document.getElementById("navLinks");
if (navToggle && navLinks) {
  navToggle.addEventListener("click", () => navLinks.classList.toggle("open"));
  navLinks.querySelectorAll("a").forEach((a) => {
    a.addEventListener("click", () => navLinks.classList.remove("open"));
  });
}

const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const videos = document.querySelectorAll("video[data-src]");
if (!reduce && videos.length && "IntersectionObserver" in window) {
  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        const video = entry.target;
        if (!entry.isIntersecting) {
          video.pause();
          return;
        }
        if (!video.src) {
          video.src = video.dataset.src;
          video.addEventListener("playing", () => video.classList.add("on"), { once: true });
        }
        video.play().catch(() => {});
      });
    },
    { rootMargin: "120px", threshold: 0.25 }
  );
  videos.forEach((video) => io.observe(video));
}

const thread = document.getElementById("thread");
const agentForm = document.getElementById("agentForm");
const agentInput = document.getElementById("agentInput");
const agentSend = document.getElementById("agentSend");
const history = [
  {
    role: "assistant",
    content: "I'm Vela. I live on this page. Ask me about the cast, the coin, or the doll still sitting in the weights.",
  },
];

function paintThread() {
  if (!thread) return;
  thread.replaceChildren();
  history.forEach((message) => {
    const bubble = document.createElement("p");
    bubble.className = `bubble ${message.role === "user" ? "you" : "vela"}`;
    bubble.textContent = message.content;
    thread.appendChild(bubble);
  });
  thread.scrollTop = thread.scrollHeight;
}

async function askVela(text) {
  const content = text.trim().slice(0, 500);
  if (!content || !agentSend) return;
  history.push({ role: "user", content });
  paintThread();
  agentSend.disabled = true;
  agentInput.value = "";
  const pending = document.createElement("p");
  pending.className = "bubble vela";
  pending.textContent = "…";
  thread.appendChild(pending);
  thread.scrollTop = thread.scrollHeight;
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        messages: history.slice(-8),
      }),
    });
    const data = await res.json().catch(() => ({}));
    pending.remove();
    if (!res.ok || !data.reply) {
      const err = document.createElement("p");
      err.className = "bubble err";
      err.textContent = data.error || "Vela dropped the line.";
      thread.appendChild(err);
      history.pop();
    } else {
      history.push({ role: "assistant", content: data.reply });
      paintThread();
    }
  } catch {
    pending.remove();
    history.pop();
    const err = document.createElement("p");
    err.className = "bubble err";
    err.textContent = "Vela dropped the line.";
    thread.appendChild(err);
  } finally {
    agentSend.disabled = false;
    agentInput.focus();
  }
}

if (thread && agentForm && agentInput) {
  paintThread();
  agentForm.addEventListener("submit", (event) => {
    event.preventDefault();
    askVela(agentInput.value);
  });
  document.querySelectorAll("[data-ask]").forEach((button) => {
    button.addEventListener("click", () => askVela(button.dataset.ask || ""));
  });
}
