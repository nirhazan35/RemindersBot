const { default: makeWASocket, useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion } = require("@whiskeysockets/baileys");
const qrcode = require("qrcode-terminal");
const fetch = (...args) => import('node-fetch').then(({default: f}) => f(...args));

let sock = null;
let ready = false;
let lastQR = null;

async function startBaileys() {
  try {
    const { state, saveCreds } = await useMultiFileAuthState("auth_info_baileys");
    const { version } = await fetchLatestBaileysVersion();
    
    sock = makeWASocket({ 
      version, 
      auth: state,
      printQRInTerminal: true,
      defaultQueryTimeoutMs: 60_000,
    });

  sock.ev.on("creds.update", saveCreds);

  sock.ev.on("connection.update", ({ connection, lastDisconnect, qr }) => {
    if (qr) {
      lastQR = qr;
      qrcode.generate(qr, { small: true });
      console.log("Scan the QR above to login.");
    }
    if (connection === "open") { 
      ready = true; 
      console.log("✅ WhatsApp connected"); 
    }
    if (connection === "close") {
      ready = false;
      lastQR = null;
      const shouldReconnect = (lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut);
      
      // Log the disconnect reason for debugging
      console.log("Connection closed. Reason:", lastDisconnect?.error?.output?.statusCode);
      console.log("Should reconnect:", shouldReconnect);
      
      if (shouldReconnect) {
        console.log("Attempting to reconnect in 5 seconds...");
        setTimeout(() => startBaileys(), 5000);
      }
    }
  });

  // Forward inbound messages to Python webhook if configured
  const pyWebhook = process.env.WA_PY_WEBHOOK_URL;
  const shared = process.env.WA_SHARED_SECRET;
  if (pyWebhook && shared) {
    sock.ev.on("messages.upsert", async (m) => {
      const msg = m.messages?.[0];
      if (!msg || msg.key.fromMe) return;
      
      let payload = {
        from: msg.key.remoteJid,
        timestamp: Number(msg.messageTimestamp || Date.now())
      };

      // Handle text messages only
      if (msg.message?.conversation || msg.message?.extendedTextMessage?.text) {
        payload.type = "text";
        payload.text = msg.message?.conversation || msg.message?.extendedTextMessage?.text || "";
      }
      // Skip non-text messages
      else {
        console.log("Non-text message type, skipping:", Object.keys(msg.message || {}));
        return;
      }

      console.log("Forwarding message to Python webhook:", payload);

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
  } catch (error) {
    console.error("Error starting Baileys:", error);
    // Clear auth data if there's a persistent connection error
    if (error.message.includes("Connection Failure")) {
      console.log("Clearing corrupted auth data...");
      const fs = require('fs');
      const path = require('path');
      const authPath = path.join(__dirname, 'auth_info_baileys');
      if (fs.existsSync(authPath)) {
        fs.rmSync(authPath, { recursive: true, force: true });
      }
      console.log("Auth data cleared. Restart the container to get a fresh QR code.");
    }
  }
}

function getSock() { return sock; }
function isReady() { return ready; }
function getLastQR() { return lastQR; }

module.exports = { startBaileys, getSock, isReady, getLastQR };