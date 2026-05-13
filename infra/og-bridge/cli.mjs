#!/usr/bin/env node
/**
 * DataMind 0G Storage bridge.
 *
 * Uses @0gfoundation/0g-storage-ts-sdk (see https://build.0g.ai/storage/).
 *
 * Subcommands:
 *   upload   --file <path>  [--rpc] [--indexer] [--key]
 *      Stdout (single JSON line): {root, tx_hash, size, mode}
 *
 *   download --root <0x..>  --out <path> [--indexer]
 *      Stdout (single JSON line): {ok: true, path}
 *
 *   serve    [--port 8200]
 *      Long-running HTTP server exposing the same operations.
 *
 * Environment fallbacks for any missing flag:
 *   OG_EVM_RPC, OG_INDEXER_RPC, OG_PRIVATE_KEY
 */
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { createHash } from "node:crypto";
import http from "node:http";

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith("--")) {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (next && !next.startsWith("--")) {
        out[key] = next;
        i++;
      } else {
        out[key] = true;
      }
    }
  }
  return out;
}

function emit(obj) {
  process.stdout.write(JSON.stringify(obj) + "\n");
}

function deterministicRoot(buf) {
  return "0x" + createHash("sha256").update(buf).digest("hex");
}

function deterministicTx(root) {
  return "0x" + createHash("sha256").update("tx::" + root).digest("hex");
}

async function loadSdk() {
  try {
    const sdk = await import("@0gfoundation/0g-storage-ts-sdk");
    const { ethers } = await import("ethers");
    return { sdk, ethers };
  } catch (_e) {
    return null;
  }
}

/** @returns {{ root: string, tx_hash: string, size: number }} */
async function liveUploadFile(absPath, rpc, indexerUrl, pk) {
  const { ZgFile, Indexer } = await import("@0gfoundation/0g-storage-ts-sdk");
  const { ethers } = await import("ethers");
  const buf = readFileSync(absPath);
  const zgFile = await ZgFile.fromFilePath(absPath);
  try {
    const provider = new ethers.JsonRpcProvider(rpc);
    const wallet = new ethers.Wallet(pk, provider);
    const idx = new Indexer(indexerUrl);
    const [result, uploadErr] = await idx.upload(zgFile, rpc, wallet);
    if (uploadErr) {
      throw new Error("upload: " + (uploadErr.message || String(uploadErr)));
    }
    let root = "";
    let tx_hash = "";
    if (result && typeof result === "object") {
      if ("rootHash" in result && result.rootHash) {
        root = String(result.rootHash);
        tx_hash = String(result.txHash || "");
      } else if (
        "rootHashes" in result &&
        Array.isArray(result.rootHashes) &&
        result.rootHashes.length
      ) {
        root = String(result.rootHashes[0]);
        const txs = result.txHashes;
        tx_hash = txs && txs.length ? String(txs[0]) : "";
      }
    }
    if (!root) {
      throw new Error("upload: indexer returned no rootHash");
    }
    return { root, tx_hash, size: buf.length };
  } finally {
    try {
      await zgFile.close();
    } catch (_e) {
      /* ignore */
    }
  }
}

async function cmdUpload(args) {
  const file = args.file || args.f;
  if (!file) {
    const detail = { error: "usage", detail: "upload --file <path>" };
    console.error(JSON.stringify(detail));
    emit(detail);
    process.exit(2);
  }
  const path = resolve(file);
  if (!existsSync(path)) {
    const detail = { error: "not_found", detail: path };
    console.error(JSON.stringify(detail));
    emit(detail);
    process.exit(2);
  }
  const buf = readFileSync(path);

  const rpc = args.rpc || process.env.OG_EVM_RPC || "";
  const indexer = args.indexer || process.env.OG_INDEXER_RPC || "";
  const pk = args.key || process.env.OG_PRIVATE_KEY || "";

  if (!rpc || !indexer || !pk) {
    emit({
      root: deterministicRoot(buf),
      tx_hash: deterministicTx(deterministicRoot(buf)),
      size: buf.length,
      mode: "mock",
      reason: "missing rpc/indexer/key",
    });
    return;
  }

  const loaded = await loadSdk();
  if (!loaded) {
    emit({
      root: deterministicRoot(buf),
      tx_hash: deterministicTx(deterministicRoot(buf)),
      size: buf.length,
      mode: "mock",
      reason: "@0gfoundation/0g-storage-ts-sdk not installed",
    });
    return;
  }

  try {
    const { root, tx_hash, size } = await liveUploadFile(path, rpc, indexer, pk);
    emit({ root, tx_hash, size, mode: "live" });
  } catch (e) {
    emit({
      root: deterministicRoot(buf),
      tx_hash: deterministicTx(deterministicRoot(buf)),
      size: buf.length,
      mode: "mock-fallback",
      error: String(e && e.message ? e.message : e),
    });
  }
}

async function cmdDownload(args) {
  const root = args.root;
  const out = args.out;
  if (!root || !out) {
    emit({ error: "usage", detail: "download --root 0x... --out <path>" });
    process.exit(2);
  }
  mkdirSync(dirname(out), { recursive: true });

  const indexer = args.indexer || process.env.OG_INDEXER_RPC || "";
  if (!indexer) {
    emit({ ok: false, error: "missing indexer", root });
    process.exit(1);
  }
  const loaded = await loadSdk();
  if (!loaded) {
    emit({ ok: false, error: "sdk_unavailable", root });
    process.exit(1);
  }

  try {
    const { Indexer } = await import("@0gfoundation/0g-storage-ts-sdk");
    const idx = new Indexer(indexer);
    const err = await idx.download(root, out, true);
    if (err) throw new Error(String(err));
    emit({ ok: true, path: out, mode: "live" });
  } catch (e) {
    emit({ ok: false, error: String(e && e.message ? e.message : e) });
    process.exit(1);
  }
}

async function cmdServe(args) {
  const port = parseInt(args.port || process.env.OG_BRIDGE_PORT || "8200", 10);
  const server = http.createServer((req, res) => {
    if (req.method === "GET" && req.url === "/healthz") {
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ status: "ok" }));
      return;
    }
    if (req.method === "POST" && req.url === "/upload") {
      let body = "";
      req.on("data", (c) => (body += c));
      req.on("end", async () => {
        try {
          const { file } = JSON.parse(body || "{}");
          if (!file) {
            res.writeHead(400);
            return res.end(JSON.stringify({ error: "missing file" }));
          }
          const abs = resolve(file);
          const buf = readFileSync(abs);
          const rpc = process.env.OG_EVM_RPC || "";
          const indexer = process.env.OG_INDEXER_RPC || "";
          const pk = process.env.OG_PRIVATE_KEY || "";
          if (!rpc || !indexer || !pk) {
            const root = deterministicRoot(buf);
            res.end(
              JSON.stringify({
                root,
                tx_hash: deterministicTx(root),
                size: buf.length,
                mode: "mock",
              })
            );
            return;
          }
          if (!(await loadSdk())) {
            const root = deterministicRoot(buf);
            res.end(
              JSON.stringify({
                root,
                tx_hash: deterministicTx(root),
                size: buf.length,
                mode: "mock",
              })
            );
            return;
          }
          const { root, tx_hash, size } = await liveUploadFile(abs, rpc, indexer, pk);
          res.writeHead(200, { "Content-Type": "application/json" });
          res.end(
            JSON.stringify({
              root,
              tx_hash,
              size,
              mode: "live",
            })
          );
        } catch (e) {
          res.writeHead(500);
          res.end(JSON.stringify({ error: String(e?.message || e) }));
        }
      });
      return;
    }
    res.writeHead(404);
    res.end(JSON.stringify({ error: "not found" }));
  });
  server.listen(port, () => {
    console.log(`og-bridge listening on :${port}`);
  });
}

const [, , cmd, ...rest] = process.argv;
const args = parseArgs(rest);

switch (cmd) {
  case "upload":
    await cmdUpload(args);
    break;
  case "download":
    await cmdDownload(args);
    break;
  case "serve":
    await cmdServe(args);
    break;
  default:
    emit({ error: "usage", detail: "datamind-og {upload|download|serve}" });
    process.exit(2);
}
