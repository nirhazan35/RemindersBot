const { default: makeWASocket, useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion } = require("@whiskeysockets/baileys");
const qrcode = require("qrcode-terminal");
const fetch = (...args) => import('node-fetch').then(({default: f}) => f(...args));

let sock = null;
let ready = false;
let lastQR = null;

async function startBaileys() {
  const { state, saveCreds } = await useMultiFileAuthState("auth_info_baileys");
  const { version } = await fetchLatestBaileysVersion();
  sock = makeWASocket({ version, auth: state });

  sock.ev.on("creds.update", saveCreds);

  sock.ev.on("connection.update", ({ connection, lastDisconnect, qr }) => {
    if (qr) {
      lastQR = qr;
      qrcode.generate(qr, { small: true });
      console.log("Scan the QR above to login.");
    }
    if (connection === "open") { ready = true; console.log("✅ WhatsApp connected"); }
    if (connection === "close") {
      ready = false;
      const shouldReconnect = (lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut);
      if (shouldReconnect) startBaileys();
    }
  });

  // Forward inbound messages to Python webhook if configured
  const pyWebhook = process.env.WA_PY_WEBHOOK_URL;
  const shared = process.env.WA_SHARED_SECRET;
  if (pyWebhook && shared) {
    sock.ev.on("messages.upsert", async (m) => {
      const msg = m.messages?.[0];
      if (!msg || msg.key.fromMe) return;
      const payload = {
        from: msg.key.remoteJid,
        text: msg.message?.conversation || msg.message?.extendedTextMessage?.text || "",
        timestamp: Number(msg.messageTimestamp || Date.now())
      };
      try {
        await fetch(pyWebhook, {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-Token": shared },
          body: JSON.stringify(payload)
        });
      } catch (e) {
        console.error("Failed to call Python webhook", e);
      }
    });
  }
}

function getSock() { return sock; }
function isReady() { return ready; }
function getLastQR() { return lastQR; }

module.exports = { startBaileys, getSock, isReady, getLastQR };