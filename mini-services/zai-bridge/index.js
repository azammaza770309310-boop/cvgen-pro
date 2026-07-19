// zai-bridge: exposes the z-ai-web-dev-sdk as a local HTTP endpoint
// so the Python FastAPI app can use it as a Cloud AI provider.
// Runs on port 3030.

const http = require("http");
const ZAI = require("z-ai-web-dev-sdk").default;

let zaiInstance = null;
async function getZAI() {
  if (!zaiInstance) zaiInstance = await ZAI.create();
  return zaiInstance;
}

const server = http.createServer(async (req, res) => {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  if (req.method === "OPTIONS") { res.writeHead(204); res.end(); return; }
  if (req.method !== "POST") { res.writeHead(405); res.end("Method not allowed"); return; }

  let body = "";
  for await (const chunk of req) body += chunk;
  let payload;
  try { payload = JSON.parse(body); } catch (e) { res.writeHead(400); res.end(JSON.stringify({ error: "Invalid JSON" })); return; }

  try {
    const zai = await getZAI();
    const completion = await zai.chat.completions.create({
      messages: payload.messages,
      thinking: { type: "disabled" },
    });
    const content = completion.choices?.[0]?.message?.content || "";
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ success: true, content }));
  } catch (e) {
    res.writeHead(502, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ success: false, error: e.message }));
  }
});

server.listen(3030, () => console.log("zai-bridge listening on :3030"));
