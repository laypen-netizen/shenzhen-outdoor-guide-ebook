#!/usr/bin/env node

const DEBUG_ORIGIN = process.env.CHROME_DEBUG_ORIGIN || "http://127.0.0.1:9231";
const SITE_ORIGIN = process.env.SITE_ORIGIN || "http://127.0.0.1:4173";

class CdpSession {
  constructor(webSocketUrl) {
    this.socket = new WebSocket(webSocketUrl);
    this.nextId = 1;
    this.pending = new Map();
    this.listeners = new Map();
  }

  async connect() {
    await new Promise((resolve, reject) => {
      this.socket.addEventListener("open", resolve, { once: true });
      this.socket.addEventListener("error", reject, { once: true });
    });
    this.socket.addEventListener("message", ({ data }) => {
      const message = JSON.parse(data);
      if (message.id) {
        const pending = this.pending.get(message.id);
        if (!pending) return;
        this.pending.delete(message.id);
        if (message.error) pending.reject(new Error(message.error.message));
        else pending.resolve(message.result);
        return;
      }
      for (const listener of this.listeners.get(message.method) || []) {
        listener(message.params || {});
      }
    });
  }

  send(method, params = {}) {
    const id = this.nextId++;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.socket.send(JSON.stringify({ id, method, params }));
    });
  }

  waitFor(method, timeoutMs = 10000) {
    return new Promise((resolve, reject) => {
      const listeners = this.listeners.get(method) || [];
      const timeout = setTimeout(() => {
        this.listeners.set(method, listeners.filter((item) => item !== onEvent));
        reject(new Error(`Timed out waiting for ${method}`));
      }, timeoutMs);
      const onEvent = (params) => {
        clearTimeout(timeout);
        this.listeners.set(method, listeners.filter((item) => item !== onEvent));
        resolve(params);
      };
      listeners.push(onEvent);
      this.listeners.set(method, listeners);
    });
  }

  async close() {
    if (this.socket.readyState === WebSocket.CLOSED) return;
    await new Promise((resolve) => {
      const timeout = setTimeout(resolve, 1000);
      this.socket.addEventListener("close", () => {
        clearTimeout(timeout);
        resolve();
      }, { once: true });
      this.socket.close();
    });
  }
}

async function createTarget(url) {
  const endpoint = `${DEBUG_ORIGIN}/json/new?${encodeURIComponent(url)}`;
  const response = await fetch(endpoint, { method: "PUT" });
  if (!response.ok) throw new Error(`Cannot create Chrome target: ${response.status}`);
  return response.json();
}

async function closeTarget(targetId) {
  const response = await fetch(`${DEBUG_ORIGIN}/json/close/${encodeURIComponent(targetId)}`);
  if (!response.ok) throw new Error(`Cannot close Chrome target: ${response.status}`);
}

async function siteTargetCount() {
  const response = await fetch(`${DEBUG_ORIGIN}/json/list`);
  if (!response.ok) throw new Error(`Cannot list Chrome targets: ${response.status}`);
  const targets = await response.json();
  return targets.filter((target) => target.type === "page" && target.url.startsWith(SITE_ORIGIN)).length;
}

async function evaluate(session, expression) {
  const result = await session.send("Runtime.evaluate", {
    expression,
    awaitPromise: true,
    returnByValue: true,
  });
  if (result.exceptionDetails) throw new Error(result.exceptionDetails.text);
  return result.result.value;
}

async function inspectPage(path, viewport) {
  const target = await createTarget(`${SITE_ORIGIN}${path}`);
  try {
    return await inspectTarget(target, path, viewport);
  } finally {
    await closeTarget(target.id);
  }
}

async function inspectTarget(target, path, viewport) {
  const session = new CdpSession(target.webSocketDebuggerUrl);
  try {
    await session.connect();
    return await inspectSession(session, path, viewport);
  } finally {
    await session.close();
  }
}

async function inspectSession(session, path, viewport) {
  const browserErrors = [];
  const networkRequests = new Map();
  session.listeners.set("Runtime.exceptionThrown", [({ exceptionDetails }) => {
    browserErrors.push(`exception: ${exceptionDetails?.text || "unknown"}`);
  }]);
  session.listeners.set("Log.entryAdded", [({ entry }) => {
    if (entry?.level === "error") browserErrors.push(`log: ${entry.text}`);
  }]);
  session.listeners.set("Runtime.consoleAPICalled", [({ type, args }) => {
    if (type === "error") {
      browserErrors.push(`console: ${args.map((arg) => arg.value || arg.description).join(" ")}`);
    }
  }]);
  session.listeners.set("Network.responseReceived", [({ requestId, response, type }) => {
    if (response?.url?.startsWith(SITE_ORIGIN)) {
      networkRequests.set(requestId, {
        url: response.url,
        type,
        bytes: 0,
      });
    }
  }]);
  session.listeners.set("Network.loadingFinished", [({ requestId, encodedDataLength }) => {
    const request = networkRequests.get(requestId);
    if (request) request.bytes = encodedDataLength || 0;
  }]);

  await Promise.all([
    session.send("Page.enable"),
    session.send("Runtime.enable"),
    session.send("Log.enable"),
    session.send("Network.enable"),
  ]);
  await session.send("Network.setCacheDisabled", { cacheDisabled: true });
  await session.send("Emulation.setDeviceMetricsOverride", {
    width: viewport.width,
    height: viewport.height,
    deviceScaleFactor: viewport.deviceScaleFactor || 1,
    mobile: viewport.width <= 680,
  });

  const loaded = session.waitFor("Page.loadEventFired");
  await session.send("Page.navigate", { url: `${SITE_ORIGIN}${path}` });
  await loaded;
  await new Promise((resolve) => setTimeout(resolve, 500));

  const initialMetrics = await evaluate(session, `({
    documentHeight: document.documentElement.scrollHeight,
  })`);
  const initialTransferredBytes = [...networkRequests.values()]
    .reduce((total, request) => total + request.bytes, 0);
  const initialImageBytes = [...networkRequests.values()]
    .filter((request) => request.type === "Image")
    .reduce((total, request) => total + request.bytes, 0);

  if (viewport.width <= 680) {
    await evaluate(session, `(() => {
      const menu = document.querySelector('.menu-button');
      menu?.click();
      const filter = document.querySelector('#mobile-filter-button');
      filter?.click();
      return true;
    })()`);
  }

  let deferredFeaturedImageLoaded = null;
  if (viewport.width <= 680 && path === "/") {
    deferredFeaturedImageLoaded = await evaluate(session, `(async () => {
      for (let index = 0; index < 20; index += 1) {
        const next = Math.min(
          document.documentElement.scrollHeight - innerHeight,
          (index + 1) * innerHeight,
        );
        scrollTo(0, next);
        await new Promise((resolve) => setTimeout(resolve, 60));
        if (next >= document.documentElement.scrollHeight - innerHeight) break;
      }
      const featured = document.querySelector('.featured-grid');
      featured?.scrollIntoView({ block: 'center' });
      await new Promise((resolve) => setTimeout(resolve, 500));
      const image = featured?.querySelector('img');
      const loaded = Boolean(image?.complete && image?.naturalWidth > 0);
      scrollTo(0, 0);
      await new Promise((resolve) => setTimeout(resolve, 120));
      return loaded;
    })()`);
  }

  let interaction = null;
  if (path === "/places/") {
    interaction = await evaluate(session, `(() => {
      const input = document.querySelector('#place-search');
      input.value = '天文台';
      input.dispatchEvent(new Event('input', { bubbles: true }));
      const visibleCards = [...document.querySelectorAll('.place-card')]
        .filter((card) => !card.hidden).length;
      return {
        visibleCards,
        resultsText: document.querySelector('#results-count')?.textContent.trim() || '',
        query: location.search,
        filterExpanded: document.querySelector('#mobile-filter-button')?.getAttribute('aria-expanded') || null,
      };
    })()`);
  }

  const audit = await evaluate(session, `(() => {
    const visible = (element) => {
      const style = getComputedStyle(element);
      const rect = element.getBoundingClientRect();
      return style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0 && rect.height > 0;
    };
    const insideHorizontalScroller = (element) => {
      let parent = element.parentElement;
      while (parent && parent !== document.body) {
        const style = getComputedStyle(parent);
        if (
          ['auto', 'scroll'].includes(style.overflowX) &&
          parent.scrollWidth > parent.clientWidth + 1
        ) return true;
        parent = parent.parentElement;
      }
      return false;
    };
    const overflowElements = [...document.querySelectorAll('body *')]
      .filter(visible)
      .map((element) => ({
        element,
        tag: element.tagName.toLowerCase(),
        className: typeof element.className === 'string' ? element.className : '',
        rect: element.getBoundingClientRect(),
      }))
      .filter(({ rect, element }) => {
        return (rect.right > innerWidth + 1 || rect.left < -1) && !insideHorizontalScroller(element);
      })
      .slice(0, 10)
      .map(({ tag, className, rect }) => ({
        tag,
        className,
        left: Math.round(rect.left),
        right: Math.round(rect.right),
      }));
    const touchTargets = [...document.querySelectorAll(
      '.menu-button, .mobile-tabbar a, .button, .mobile-filter-button, .check-label'
    )]
      .filter(visible)
      .map((element) => {
        const rect = element.getBoundingClientRect();
        return {
          label: element.textContent.trim().replace(/\\s+/g, ' ').slice(0, 40),
          width: Math.round(rect.width),
          height: Math.round(rect.height),
        };
      });
    return {
      title: document.title,
      viewportWidth: innerWidth,
      documentWidth: document.documentElement.scrollWidth,
      documentHeight: document.documentElement.scrollHeight,
      horizontalScrollers: [...document.querySelectorAll('.mobile-scroll-row')]
        .filter(visible)
        .filter((element) => element.scrollWidth > element.clientWidth + 1).length,
      heroVisualTransform: document.querySelector('.hero-visual')
        ? getComputedStyle(document.querySelector('.hero-visual')).transform
        : null,
      overflowElements,
      brokenImages: [...document.images].filter((image) => image.complete && image.naturalWidth === 0).length,
      touchTargets,
      menuExpanded: document.querySelector('.menu-button')?.getAttribute('aria-expanded') || null,
      mobileMenuVisible: document.querySelector('#mobile-menu')?.hidden === false,
    };
  })()`);

  const transferredBytes = [...networkRequests.values()]
    .reduce((total, request) => total + request.bytes, 0);
  const imageBytes = [...networkRequests.values()]
    .filter((request) => request.type === "Image")
    .reduce((total, request) => total + request.bytes, 0);
  return {
    path,
    viewport,
    ...audit,
    interaction,
    deferredFeaturedImageLoaded,
    initialDocumentHeight: initialMetrics.documentHeight,
    initialTransferredBytes,
    initialImageBytes,
    transferredBytes,
    imageBytes,
    loadedResources: networkRequests.size,
    browserErrors: [...new Set(browserErrors)],
  };
}

const siteTargetsBefore = await siteTargetCount();
const checks = [];
for (const viewport of [
  { name: "desktop", width: 1440, height: 1000, deviceScaleFactor: 1 },
  { name: "mobile", width: 390, height: 844, deviceScaleFactor: 3 },
]) {
  for (const path of ["/", "/places/", "/places/001/"]) {
    checks.push(await inspectPage(path, viewport));
  }
}
const siteTargetsAfter = await siteTargetCount();

const errors = [];
if (siteTargetsAfter !== siteTargetsBefore) {
  errors.push(`Chrome debug target leak: ${siteTargetsBefore} -> ${siteTargetsAfter}`);
}
for (const check of checks) {
  const label = `${check.viewport.name} ${check.path}`;
  if (check.documentWidth > check.viewportWidth) errors.push(`${label}: horizontal overflow`);
  if (check.overflowElements.length) errors.push(`${label}: overflowing elements`);
  if (check.brokenImages) errors.push(`${label}: ${check.brokenImages} broken images`);
  if (check.browserErrors.length) errors.push(`${label}: browser errors`);
  if (check.viewport.name === "mobile") {
    const undersized = check.touchTargets.filter(({ height }) => height < 44);
    if (undersized.length) errors.push(`${label}: touch targets below 44px`);
    if (check.menuExpanded !== "true" || !check.mobileMenuVisible) {
      errors.push(`${label}: mobile menu did not open`);
    }
    if (check.path === "/" && check.documentHeight > 6500) {
      errors.push(`${label}: homepage exceeds 6500px height budget`);
    }
    if (check.path === "/" && check.initialTransferredBytes > 900000) {
      errors.push(`${label}: homepage exceeds 900KB initial transfer budget`);
    }
    if (check.path === "/" && check.horizontalScrollers < 3) {
      errors.push(`${label}: homepage mobile scrollers are not active`);
    }
    if (check.path === "/" && check.deferredFeaturedImageLoaded !== true) {
      errors.push(`${label}: deferred featured image did not load on demand`);
    }
    if (check.path === "/places/" && check.initialTransferredBytes > 1000000) {
      errors.push(`${label}: catalog exceeds 1000KB initial transfer budget`);
    }
    if (check.path === "/places/001/" && check.initialTransferredBytes > 600000) {
      errors.push(`${label}: detail page exceeds 600KB initial transfer budget`);
    }
  }
  if (check.path === "/places/" && check.interaction?.visibleCards !== 1) {
    errors.push(`${label}: catalog filter expected 1 result`);
  }
  if (check.path === "/" && check.heroVisualTransform !== "none") {
    errors.push(`${label}: homepage hero visual must be axis-aligned`);
  }
}

console.log(JSON.stringify({
  status: errors.length ? "failed" : "ok",
  checks,
  debugTargets: { before: siteTargetsBefore, after: siteTargetsAfter },
  errors,
}, null, 2));
process.exitCode = errors.length ? 1 : 0;
