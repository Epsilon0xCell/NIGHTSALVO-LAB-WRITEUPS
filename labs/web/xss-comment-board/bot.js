#!/usr/bin/env node
/*
 * bot.js: a local simulation harness standing in for a real admin browser.
 *
 * A real stored XSS attack needs a victim, usually an admin, to open the
 * page that holds the stored payload while logged in. No real browser or
 * real admin is used here. This script plays that role instead:
 *
 *   1. It fetches http://127.0.0.1:8002/admin with a Cookie header that
 *      carries the admin session cookie.
 *   2. It extracts every <script>...</script> block from the rendered page.
 *   3. It runs those blocks in a Node vm sandbox where document.cookie
 *      returns that same cookie, and fetch really performs HTTP requests.
 *
 * That is enough for a stored payload to read document.cookie and send it
 * to the board's /collect endpoint, exactly as it would in a browser.
 * This harness is for this local lab only. Never point it at a real site.
 */

const vm = require("vm");

const ADMIN_URL = "http://127.0.0.1:8002/admin";
const ADMIN_COOKIE = "session=SALVO{st0r3d_xss_g0t_th3_c00k13}";

async function main() {
  console.log(`[bot] visiting ${ADMIN_URL}`);
  console.log(`[bot] carrying cookie: ${ADMIN_COOKIE}`);

  const response = await fetch(ADMIN_URL, {
    headers: { Cookie: ADMIN_COOKIE },
  });
  const html = await response.text();
  console.log(`[bot] /admin responded with status ${response.status}`);

  const scripts = [];
  const pattern = /<script>([\s\S]*?)<\/script>/gi;
  let match;
  while ((match = pattern.exec(html)) !== null) {
    scripts.push(match[1]);
  }
  console.log(`[bot] found ${scripts.length} script block(s) on the page`);

  const sandbox = {
    document: {
      get cookie() {
        return ADMIN_COOKIE;
      },
    },
    fetch: fetch,
    console: console,
  };
  vm.createContext(sandbox);

  for (const [index, code] of scripts.entries()) {
    console.log(`[bot] running script block ${index + 1}: ${code.trim()}`);
    try {
      vm.runInContext(code, sandbox);
    } catch (err) {
      console.log(`[bot] script block ${index + 1} errored: ${err.message}`);
    }
  }

  // Give any fetch started by a payload time to finish.
  await new Promise((resolve) => setTimeout(resolve, 1000));
  console.log("[bot] done visiting");
}

main().catch((err) => {
  console.error(`[bot] failed: ${err.message}`);
  process.exit(1);
});
