#!/usr/bin/env node
/**
 * DataMind 0G Storage bridge.
 *
 * Subcommands:
 *   upload   --file <path>  [--rpc] [--indexer] [--key]
 *      Stdout (single JSON line): {root, tx_hash, size}
 *
 *   download --root <0x..>  --out <path> [--indexer]
 *      Stdout (single JSON line): {ok: true, path}
 *
 *   serve    [--port 8200]
 *      Long-running HTTP server exposing the same operations.
 *
 * Environment fallbacks for any missing flag:
 *   OG_EVM_RPC, OG_INDEXER_RPC, OG_PRIVATE_KEY
 *
 * The Python `og_client.py` shells to this binary. In live mode it expects a
 * JSON line with mode "live"; mock / fallback lines are treated as failures.
 */
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { createHash } from "node:crypto";
import http from "node:http";

// ---------------------------------------------------------------------------
// Argument parser
// ---------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------
// Lazy SDK loader — keeps the bridge usable in mock mode without npm install.
// ---------------------------------------------------------------------------

async function loadSdk() {
  try {
    const sdk = await import("@0glabs/0g-ts-sdk");
    const { ethers } = await import("ethers");
    return { sdk, ethers };
  } catch (e) {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Upload
// ---------------------------------------------------------------------------

async function cmdUpload(args) {
  const file = args.file || args.f;
  if (!file) {
    emit({ error: "usage", detail: "upload --file <path>" });
    process.exit(2);
  }
  const path = resolve(file);
  if (!existsSync(path)) {
    emit({ error: "not_found", detail: path });
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
      reason: "@0glabs/0g-ts-sdk not installed",
    });
    return;
  }

  const { sdk, ethers } = loaded;
  try {
    const ZgFile = sdk.ZgFile || sdk.default?.ZgFile;
    const Indexer = sdk.Indexer || sdk.default?.Indexer;
    if (!ZgFile || !Indexer) {
      throw new Error("ZgFile/Indexer not exported by SDK");
    }
    const zgFile = await ZgFile.fromFilePath(path);
    const [tree, merkleErr] = await zgFile.merkleTree();
    if (merkleErr) throw new Error("merkleTree: " + merkleErr);
    const root = tree.rootHash();

    const provider = new ethers.JsonRpcProvider(rpc);
    const wallet = new ethers.Wallet(pk, provider);
    const idx = new Indexer(indexer);
    const [tx, uploadErr] = await idx.upload(zgFile, rpc, wallet);
    if (uploadErr) throw new Error("upload: " + (uploadErr.message || uploadErr));

    let tx_hash = "";
    if (tx && typeof tx === "object") {
      tx_hash = String(tx.hash || tx.txHash || tx.transactionHash || "");
    } else if (tx) {
      tx_hash = String(tx);
    }

    await zgFile.close();
    emit({ root, tx_hash, size: buf.length, mode: "live" });
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

// ---------------------------------------------------------------------------
// Download (mock-friendly)
// ---------------------------------------------------------------------------

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
    const { sdk } = loaded;
    const Indexer = sdk.Indexer || sdk.default?.Indexer;
    const idx = new Indexer(indexer);
    const err = await idx.download(root, out, true);
    if (err) throw new Error(String(err));
    emit({ ok: true, path: out, mode: "live" });
  } catch (e) {
    emit({ ok: false, error: String(e && e.message ? e.message : e) });
    process.exit(1);
  }
}

// ---------------------------------------------------------------------------
// Long-running HTTP server (used by docker compose `og-bridge` profile).
// ---------------------------------------------------------------------------

async function cmdServe(args) {
  const port = parseInt(args.port || process.env.OG_BRIDGE_PORT || "8200", 10);
  const server = http.createServer(async (req, res) => {
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
          // Reuse the upload command path.
          const buf = readFileSync(file);
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
          // Live path — same as cmdUpload, inlined for simplicity.
          const loaded = await loadSdk();
          if (!loaded) {
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
          const { sdk, ethers } = loaded;
          const ZgFile = sdk.ZgFile || sdk.default?.ZgFile;
          const Indexer = sdk.Indexer || sdk.default?.Indexer;
          const zgFile = await ZgFile.fromFilePath(file);
          const [tree] = await zgFile.merkleTree();
          const root = tree.rootHash();
          const provider = new ethers.JsonRpcProvider(rpc);
          const wallet = new ethers.Wallet(pk, provider);
          const idx = new Indexer(indexer);
          const [tx] = await idx.upload(zgFile, rpc, wallet);
          await zgFile.close();
          res.writeHead(200, { "Content-Type": "application/json" });
          res.end(
            JSON.stringify({
              root,
              tx_hash: String(tx?.hash || tx?.txHash || ""),
              size: buf.length,
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

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

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
