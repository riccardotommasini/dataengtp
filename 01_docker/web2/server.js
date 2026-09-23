const fs = require("node:fs");
const path = require("node:path");
const dns = require("node:dns").promises;
const http = require("node:http");

const publicDir = path.join(__dirname, "public");
const port = Number(process.env.PORT || 8000);
const host = process.env.HOST || "0.0.0.0";
const wordsHost = process.env.WORDS_HOST || "words";
const wordsPort = Number(process.env.WORDS_PORT || 8080);
const narrativeHost = process.env.NARRATIVE_HOST || "narrative";
const narrativePort = Number(process.env.NARRATIVE_PORT || 8181);

const mimeTypes = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".ico": "image/x-icon",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".woff2": "font/woff2"
};

const server = http.createServer(async (req, res) => {
  try {
    if (!req.url) {
      sendJson(res, 400, { error: "Missing request URL" });
      return;
    }

    const requestUrl = new URL(req.url, `http://${req.headers.host || "localhost"}`);
    console.log(`[web2] ${req.method} ${requestUrl.pathname}`);
    if (requestUrl.pathname.startsWith("/words/")) {
      await proxyWordRequest(requestUrl.pathname, res);
      return;
    }

    if (requestUrl.pathname === "/narrative") {
      await proxyNarrativeRequest(res);
      return;
    }

    await serveStatic(requestUrl.pathname, res);
  } catch (error) {
    console.error("[web2] request failed", error);
    sendJson(res, 500, { error: "Unexpected server error" });
  }
});

server.listen(port, host, () => {
  console.log(`web2 listening on http://${host}:${port}`);
});

async function proxyWordRequest(pathname, res) {
  const addresses = await dns.lookup(wordsHost, { all: true });
  if (addresses.length === 0) {
    sendJson(res, 502, { error: `No IPs found for ${wordsHost}` });
    return;
  }

  const address = addresses[Math.floor(Math.random() * addresses.length)];
  const upstreamPath = pathname.replace(/^\/words/, "") || "/";
  const upstreamUrl = `http://${address.address}:${wordsPort}${upstreamPath}`;
  console.log(`[web2] proxy words ${pathname} -> ${upstreamUrl}`);
  const upstreamResponse = await fetch(upstreamUrl);
  const body = await upstreamResponse.arrayBuffer();
  console.log(`[web2] words response ${upstreamResponse.status} from ${address.address}`);

  res.statusCode = upstreamResponse.status;
  res.setHeader("source", address.address);
  const contentType = upstreamResponse.headers.get("content-type");
  if (contentType) {
    res.setHeader("content-type", contentType);
  }
  res.end(Buffer.from(body));
}

async function proxyNarrativeRequest(res) {
  const addresses = await dns.lookup(narrativeHost, { all: true });
  if (addresses.length === 0) {
    sendJson(res, 502, { error: `No IPs found for ${narrativeHost}` });
    return;
  }

  const address = addresses[Math.floor(Math.random() * addresses.length)];
  const upstreamUrl = `http://${address.address}:${narrativePort}/narrative`;
  console.log(`[web2] proxy narrative -> ${upstreamUrl}`);
  const upstreamResponse = await fetch(upstreamUrl);
  const body = await upstreamResponse.arrayBuffer();
  console.log(`[web2] narrative response ${upstreamResponse.status} from ${address.address}`);

  res.statusCode = upstreamResponse.status;
  const contentType = upstreamResponse.headers.get("content-type");
  if (contentType) {
    res.setHeader("content-type", contentType);
  }
  res.end(Buffer.from(body));
}

async function serveStatic(pathname, res) {
  const safePath = pathname === "/" ? "/index.html" : pathname;
  const requestedPath = path.normalize(path.join(publicDir, safePath));

  if (!requestedPath.startsWith(publicDir)) {
    sendJson(res, 403, { error: "Forbidden" });
    return;
  }

  try {
    const stats = await fs.promises.stat(requestedPath);
    if (stats.isDirectory()) {
      await serveStatic(path.join(safePath, "index.html"), res);
      return;
    }

    const extension = path.extname(requestedPath);
    res.statusCode = 200;
    res.setHeader("content-type", mimeTypes[extension] || "application/octet-stream");
    fs.createReadStream(requestedPath).pipe(res);
  } catch (error) {
    if (error.code === "ENOENT") {
      sendJson(res, 404, { error: "Not found" });
      return;
    }
    throw error;
  }
}

function sendJson(res, statusCode, payload) {
  res.statusCode = statusCode;
  res.setHeader("content-type", "application/json; charset=utf-8");
  res.end(JSON.stringify(payload));
}
