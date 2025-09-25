// wa/server.js
const express = require("express");
const pino = require("pino")();
const { startBaileys, getSock, isReady, getLastQR } = require("./whatsappClient");

const SHARED = process.env.WA_SHARED_SECRET || "";
const app = express();
app.use(express.json());

(async () => { try { await startBaileys(); } catch (e) { pino.error(e); process.exit(1); }})();

function requireAuth(req, res, next) {
  if ((req.header("X-Token") || "") !== SHARED) return res.status(401).json({ error: "unauthorized" });
  next();
}

app.get("/health", (_, res) => res.json({ ok: true, ready: isReady() }));
app.get("/qr", (_, res) => res.json({ loggedIn: isReady(), qr: isReady() ? null : (getLastQR() || null) }));

// 1) Send plain text
app.post("/send/text", requireAuth, async (req, res) => {
  if (!isReady()) return res.status(503).json({ error: "not_ready" });
  const { to, text } = req.body || {};
  if (!to || !text) return res.status(400).json({ error: "missing to/text" });
  const jid = to.endsWith("@s.whatsapp.net") ? to : `${to.replace(/\D/g, "")}@s.whatsapp.net`;
  await getSock().sendMessage(jid, { text });
  res.json({ ok: true });
});

// 2) Send text + YES/NO buttons (hydrated buttons)
app.post("/send/buttons", requireAuth, async (req, res) => {
  if (!isReady()) return res.status(503).json({ error: "not_ready" });
  const { to, header, body, footer, yes_id, yes_title, no_id, no_title } = req.body || {};
  if (!to || !body || !yes_id || !no_id) return res.status(400).json({ error: "missing fields" });

  const jid = to.endsWith("@s.whatsapp.net") ? to : `${to.replace(/\D/g, "")}@s.whatsapp.net`;

  const buttons = [
    { quickReplyButton: { displayText: yes_title || "כן", id: yes_id } },
    { quickReplyButton: { displayText: no_title  || "לא",  id: no_id  } },
  ];

  await getSock().sendMessage(jid, {
    templateMessage: {
      hydratedTemplate: {
        hydratedTitle: header || "אישור שליחת תזכורת",
        hydratedContentText: body,
        hydratedFooterText: footer || "בחר/י אופציה.",
        hydratedButtons: buttons
      }
    }
  });

  res.json({ ok: true });
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => pino.info(`WA adapter on :${PORT}`));