// wa/server.js
const express = require("express");
const pino = require("pino")();
const QRCode = require('qrcode');
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

// QR code endpoint - returns scannable QR code as HTML page
app.get("/qr", async (_, res) => {
  try {
    if (isReady()) {
      res.status(200).send(`
        <html>
          <body style="text-align: center; font-family: Arial;">
            <h2>✅ WhatsApp is already connected!</h2>
            <p>No need to scan QR code.</p>
          </body>
        </html>
      `);
      return;
    }

    const qrData = getLastQR();
    if (!qrData) {
      res.status(503).send(`
        <html>
          <body style="text-align: center; font-family: Arial;">
            <h2>❌ QR Code not available</h2>
            <p>WhatsApp adapter is starting up. Please wait a moment and refresh.</p>
            <button onclick="location.reload()">Refresh</button>
          </body>
        </html>
      `);
      return;
    }

    // Generate QR code as PNG
    const qrCodeDataURL = await QRCode.toDataURL(qrData, {
      width: 300,
      margin: 2
    });

    res.status(200).send(`
      <html>
        <head>
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <title>WhatsApp QR Code</title>
        </head>
        <body style="text-align: center; font-family: Arial; padding: 20px;">
          <h2>📱 Scan QR Code with WhatsApp</h2>
          <p>Open WhatsApp → Menu → Linked Devices → Link a Device</p>
          <img src="${qrCodeDataURL}" alt="WhatsApp QR Code" style="max-width: 100%; height: auto;" />
          <br><br>
          <button onclick="location.reload()" style="padding: 10px 20px; font-size: 16px;">
            🔄 Refresh QR Code
          </button>
          <script>
            // Auto-refresh every 30 seconds
            setTimeout(() => location.reload(), 30000);
          </script>
        </body>
      </html>
    `);
  } catch (error) {
    console.error("Error generating QR image:", error);
    res.status(500).send(`
      <html>
        <body style="text-align: center; font-family: Arial;">
          <h2>❌ Error generating QR code</h2>
          <p>${error.message}</p>
        </body>
      </html>
    `);
  }
});

// Send plain text messages
app.post("/send/text", requireAuth, async (req, res) => {
  if (!isReady()) return res.status(503).json({ error: "not_ready" });
  const { to, text } = req.body || {};
  if (!to || !text) return res.status(400).json({ error: "missing to/text" });
  const jid = to.endsWith("@s.whatsapp.net") ? to : `${to.replace(/\D/g, "")}@s.whatsapp.net`;
  await getSock().sendMessage(jid, { text });
  res.json({ ok: true });
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => pino.info(`WA adapter on :${PORT}`));