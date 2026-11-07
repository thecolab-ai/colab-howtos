// Colab How-Tos viewer. MIT licence, written for this repo.
//
// Reads data/content.json (written by scripts/build_site.py) and the markdown files it
// points at, plus data/issues.json if the Pages build fetched it. Hash routes, relative
// paths only, so it works under any base path such as /colab-howtos/:
//   #/                     home (?status=, ?tag= filter modules; ?s= scrolls to a section)
//   #/recap/<YYYY-Www>     one recap (?s=<heading id>)
//   #/module/<id>          one module and its lessons (?s=<heading id>)

import { escapeHtml as esc, renderMarkdown } from "./md.js";

const STATUSES = ["seed", "draft", "tested"];
const STATUS_HELP = {
  seed: "An outline from the recap. Nobody has run the steps yet.",
  draft: "Written up and partly worked through. Untested steps are marked.",
  tested: "A contributor ran every step, on the date in the module's Notes.",
};
const MONTH = new Intl.DateTimeFormat("en-NZ", { month: "short", timeZone: "UTC" });

const app = document.getElementById("app");
const main = document.getElementById("main");
const state = { content: null, issues: undefined, text: new Map(), firstRender: true };

// --- data -------------------------------------------------------------------------

async function getJson(path) {
  const response = await fetch(path, { cache: "no-cache" });
  if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
  return response.json();
}

async function getText(path) {
  if (!state.text.has(path)) {
    state.text.set(
      path,
      fetch(path, { cache: "no-cache" }).then((r) => {
        if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
        return r.text();
      }),
    );
  }
  return state.text.get(path);
}

async function loadIssues() {
  if (state.issues === undefined) {
    try {
      state.issues = await getJson("data/issues.json");
      if (!Array.isArray(state.issues)) state.issues = null;
    } catch {
      state.issues = null; // Not fetched at build time: link to GitHub instead.
    }
  }
  return state.issues;
}

const repoUrl = () => `https://github.com/${state.content?.repo || "thecolab-ai/colab-howtos"}`;
const issuesUrl = () => `${repoUrl()}/issues?q=is%3Aopen+label%3Amodule`;
const realModules = () => state.content.modules.filter((m) => !m.example);
const findRecap = (week) => state.content.recaps.find((r) => r.week === week);
const findModule = (id) => state.content.modules.find((m) => m.id === id);

// --- formatting -------------------------------------------------------------------

function utcDate(iso) {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d));
}

function dateRange(start, end) {
  const a = utcDate(start);
  const b = utcDate(end);
  const year = b.getUTCFullYear();
  if (a.getUTCMonth() === b.getUTCMonth()) return `${a.getUTCDate()} to ${b.getUTCDate()} ${MONTH.format(b)} ${year}`;
  const startYear = a.getUTCFullYear() !== year ? ` ${a.getUTCFullYear()}` : "";
  return `${a.getUTCDate()} ${MONTH.format(a)}${startYear} to ${b.getUTCDate()} ${MONTH.format(b)} ${year}`;
}

function weekLabel(week) {
  const [year, number] = week.split("-W");
  return `Week ${Number(number)}, ${year}`;
}

function listJoin(items) {
  if (items.length < 2) return items.join("");
  return `${items.slice(0, -1).join(", ")} and ${items[items.length - 1]}`;
}

const badge = (status) =>
  STATUSES.includes(status)
    ? `<span class="badge badge-${status}" title="${esc(STATUS_HELP[status])}">${esc(status)}</span>`
    : "";

// --- routing ----------------------------------------------------------------------

function parseRoute() {
  const raw = location.hash.replace(/^#\/?/, "");
  const [path, query = ""] = raw.split("?");
  const parts = path.split("/").filter(Boolean).map(decodeURIComponent);
  const params = new URLSearchParams(query);
  if (parts.length === 0) return { name: "home", params };
  if (parts[0] === "recap" && parts[1]) return { name: "recap", id: parts[1], params };
  if (parts[0] === "module" && parts[1]) return { name: "module", id: parts[1], params };
  return { name: "missing", params };
}

function routeHash(name, id, params) {
  const base = name === "home" ? "#/" : `#/${name}/${encodeURIComponent(id)}`;
  const query = params && [...params].length ? `?${params}` : "";
  return base + query;
}

// Markdown links: map repo paths onto routes or site files, send the rest to GitHub.
function linkResolver(baseDir, route) {
  return (href) => {
    if (href.startsWith("#")) {
      const params = new URLSearchParams({ s: href.slice(1) });
      return routeHash(route.name, route.id, params);
    }
    if (/^[a-z][a-z0-9+.-]*:/i.test(href) || href.startsWith("//")) return href;
    const url = new URL(href, `https://repo.invalid/${baseDir}`);
    if (url.host !== "repo.invalid") return href;
    const path = decodeURIComponent(url.pathname.slice(1));
    const anchor = url.hash ? `?s=${encodeURIComponent(url.hash.slice(1))}` : "";
    let match = /^recaps\/(\d{4}-W\d{2})\.md$/.exec(path);
    if (match && findRecap(match[1])) return `#/recap/${match[1]}${anchor}`;
    match = /^modules\/([^/]+)\/?(?:[^/]+\.md|manifest\.json)?$/.exec(path);
    if (match && findModule(match[1])) return `#/module/${match[1]}${anchor}`;
    if (/^(?:modules|courses|recaps)\//.test(path)) return path;
    return `${repoUrl()}/blob/main/${path}${url.hash}`;
  };
}

function imageResolver(baseDir) {
  return (src) => {
    if (/^[a-z][a-z0-9+.-]*:/i.test(src) || src.startsWith("//")) return src;
    const url = new URL(src, `https://repo.invalid/${baseDir}`);
    return url.host === "repo.invalid" ? url.pathname.slice(1) : src;
  };
}

const issueRule = {
  re: /ISSUE\(([a-z0-9]+(?:-[a-z0-9]+)*)\)/g,
  html: (m) =>
    `<a class="issue-chip" href="${esc(`${issuesUrl()}+${m[1]}`)}" rel="noopener">the module issue (link coming soon)</a>`,
};

function markdown(source, baseDir, route, extra = {}) {
  return renderMarkdown(source, {
    link: linkResolver(baseDir, route),
    image: imageResolver(baseDir),
    inline: [issueRule],
    ...extra,
  });
}

// Split "# Title\n..." into the title and the rest.
function splitTitle(source) {
  const match = /^# (.+)\n?/.exec(source);
  return match ? [match[1].trim(), source.slice(match[0].length)] : ["", source];
}

// --- views ------------------------------------------------------------------------

function recapCard(recap, headingLevel = 3) {
  const h = `h${headingLevel}`;
  return `<li class="card recap-card">
    <a class="card-link" href="#/recap/${esc(recap.week)}">
      <p class="eyebrow">${esc(weekLabel(recap.week))} <span class="dot" aria-hidden="true">·</span> ${esc(dateRange(recap.start, recap.end))}</p>
      <${h} class="card-title">${esc(recap.title)}</${h}>
    </a>
  </li>`;
}

function moduleCard(module) {
  const tags = module.tags.map((t) => `<li>${esc(t)}</li>`).join("");
  return `<li class="card module-card">
    <a class="card-link" href="#/module/${esc(module.id)}">
      <div class="card-meta">${badge(module.status)}<span class="muted">${esc(module.difficulty || "")}</span></div>
      <h3 class="card-title">${esc(module.title)}</h3>
      <p class="card-text">${esc(module.description)}</p>
    </a>
    <ul class="tags" aria-label="Tags">${tags}</ul>
  </li>`;
}

async function latestRecapBlock(recap) {
  let sections = "";
  try {
    const holder = document.createElement("div");
    holder.innerHTML = markdown(await getText(recap.path), "recaps/", { name: "recap", id: recap.week });
    const items = [...holder.querySelectorAll("h2")].map(
      (h) => `<li><a href="#/recap/${esc(recap.week)}?s=${encodeURIComponent(h.id)}">${esc(h.textContent)}</a></li>`,
    );
    if (items.length) sections = `<h3 class="small-heading">In this recap</h3><ul class="section-list">${items.join("")}</ul>`;
  } catch {
    sections = "";
  }
  return `<section class="feature" aria-labelledby="latest-title">
    <p class="eyebrow">Latest recap <span class="dot" aria-hidden="true">·</span> ${esc(weekLabel(recap.week))} <span class="dot" aria-hidden="true">·</span> ${esc(dateRange(recap.start, recap.end))}</p>
    <h2 id="latest-title" class="feature-title"><a href="#/recap/${esc(recap.week)}">${esc(recap.title)}</a></h2>
    ${recap.summary ? `<p class="lede">${esc(recap.summary)}</p>` : ""}
    <p><a class="button primary" href="#/recap/${esc(recap.week)}">Read the recap</a></p>
    ${sections}
  </section>`;
}

function filtersHtml(modules, params) {
  const status = params.get("status") || "";
  const tag = params.get("tag") || "";
  const tags = [...new Set(modules.flatMap((m) => m.tags))].sort();
  const statusButtons = ["", ...STATUSES]
    .map(
      (s) =>
        `<button type="button" class="chip" data-status="${s}" aria-pressed="${s === status}">${s ? esc(s) : "All"}</button>`,
    )
    .join("");
  const tagOptions = ['<option value="">All tags</option>']
    .concat(tags.map((t) => `<option value="${esc(t)}"${t === tag ? " selected" : ""}>${esc(t)}</option>`))
    .join("");
  return `<div class="filters">
    <div class="filter-group" role="group" aria-label="Filter by status">${statusButtons}</div>
    <label class="filter-select"><span class="visually-hidden">Filter by tag</span>
      <select data-tag>${tagOptions}</select></label>
  </div>`;
}

function moduleGridHtml(modules, params) {
  const status = params.get("status") || "";
  const tag = params.get("tag") || "";
  if (!modules.length) {
    return `<div class="empty"><p><strong>No modules yet.</strong> Modules arrive from contributors.
      Pick a technique from <a href="#/?s=help-wanted">Help wanted</a> and build the first one.</p></div>`;
  }
  const shown = modules.filter((m) => (!status || m.status === status) && (!tag || m.tags.includes(tag)));
  if (!shown.length) {
    return `<div class="empty"><p>No modules match these filters. <a href="#/?s=modules" data-clear-filters>Clear filters</a></p></div>`;
  }
  return `<p class="muted count">${shown.length} of ${modules.length} module${modules.length === 1 ? "" : "s"}</p>
    <ul class="grid">${shown.map(moduleCard).join("")}</ul>`;
}

function issuesHtml(issues) {
  const all = `<a href="${esc(issuesUrl())}" rel="noopener">All open module issues on GitHub</a>`;
  if (issues === null) {
    return `<p>See the <a href="${esc(issuesUrl())}" rel="noopener">open module issues on GitHub</a>. Each one is a technique from a recap, waiting for someone to build it.</p>`;
  }
  if (!issues.length) return `<p>No open module issues right now. ${all}.</p>`;
  const items = issues
    .map((issue) => {
      const flag = issue.claimed
        ? '<span class="badge badge-claimed">Claimed</span>'
        : issue.help_wanted
          ? '<span class="badge badge-help">Help wanted</span>'
          : "";
      const comments = issue.comments ? `<span class="muted">${issue.comments} comment${issue.comments === 1 ? "" : "s"}</span>` : "";
      return `<li class="issue">
        <a class="issue-link" href="${esc(issue.url)}" rel="noopener"><span class="issue-number">#${esc(issue.number)}</span> ${esc(issue.title)}</a>
        <span class="issue-meta">${flag}${comments}</span>
      </li>`;
    })
    .join("");
  return `<ul class="issue-list">${items}</ul><p>${all}.</p>`;
}

async function renderHome(route) {
  const { recaps } = state.content;
  const modules = realModules();
  const latest = recaps[0];
  const [latestHtml, issues] = await Promise.all([latest ? latestRecapBlock(latest) : "", loadIssues()]);

  document.title = "Colab How-Tos";
  app.innerHTML = `
    <section class="hero">
      <p class="eyebrow">The Colab community</p>
      <h1 tabindex="-1">How-tos from people building with AI</h1>
      <p class="lede">Each week we write up what people in The Colab got working. Community members then turn each technique into a tested how-to module that you, or your agent, can follow.</p>
      <p class="actions">
        ${latest ? `<a class="button primary" href="#/recap/${esc(latest.week)}">Read the latest recap</a>` : ""}
        <a class="button" href="#/?s=help-wanted">Build a module</a>
      </p>
    </section>

    ${latestHtml}

    <section class="block" id="recaps" aria-labelledby="recaps-title">
      <h2 id="recaps-title" class="block-title">Recaps</h2>
      ${recaps.length ? `<ul class="recap-list">${recaps.map((r) => recapCard(r)).join("")}</ul>` : "<p>No recaps yet.</p>"}
    </section>

    <section class="block" id="modules" aria-labelledby="modules-title">
      <h2 id="modules-title" class="block-title">Modules</h2>
      <p class="muted legend">${STATUSES.map((s) => `${badge(s)} ${esc(STATUS_HELP[s])}`).join("<br>")}</p>
      ${modules.length ? filtersHtml(modules, route.params) : ""}
      <div data-grid>${moduleGridHtml(modules, route.params)}</div>
    </section>

    <section class="block" id="help-wanted" aria-labelledby="help-title">
      <h2 id="help-title" class="block-title">Help wanted</h2>
      <p class="lede">Every technique in a recap becomes an issue labelled <code>module</code> and <code>help wanted</code>. Claim one, build the module, open a pull request.</p>
      ${issuesHtml(issues)}
      <ol class="steps">
        <li><strong>Pick an issue</strong> and comment to claim it.</li>
        <li><strong>Work through the technique</strong> and test the steps.</li>
        <li><strong>Write the module</strong> in <code>modules/howto-&lt;slug&gt;/</code> and add it to the course.</li>
        <li><strong>Run the checks</strong> and open a pull request.</li>
      </ol>
      <p><a href="${esc(`${repoUrl()}/blob/main/CONTRIBUTING.md`)}" rel="noopener">How to contribute</a>
        <span class="dot" aria-hidden="true">·</span>
        <a href="${esc(`${repoUrl()}/blob/main/AGENTS.md`)}" rel="noopener">Instructions for your AI agent</a></p>
    </section>`;

  wireFilters(modules, route);
}

function wireFilters(modules, route) {
  const grid = app.querySelector("[data-grid]");
  const params = new URLSearchParams(route.params);
  params.delete("s");
  const update = () => {
    history.replaceState(null, "", routeHash("home", null, params));
    grid.innerHTML = moduleGridHtml(modules, params);
    app.querySelectorAll("[data-status]").forEach((b) => {
      b.setAttribute("aria-pressed", String(b.dataset.status === (params.get("status") || "")));
    });
    const select = app.querySelector("[data-tag]");
    if (select) select.value = params.get("tag") || "";
  };
  app.querySelectorAll("[data-status]").forEach((button) =>
    button.addEventListener("click", () => {
      if (button.dataset.status) params.set("status", button.dataset.status);
      else params.delete("status");
      update();
    }),
  );
  app.querySelector("[data-tag]")?.addEventListener("change", (event) => {
    if (event.target.value) params.set("tag", event.target.value);
    else params.delete("tag");
    update();
  });
  grid.addEventListener("click", (event) => {
    if (!event.target.closest("[data-clear-filters]")) return;
    event.preventDefault();
    params.delete("status");
    params.delete("tag");
    update();
  });
}

async function renderRecap(route) {
  const recaps = state.content.recaps;
  const index = recaps.findIndex((r) => r.week === route.id);
  if (index === -1) return renderMissing(`There is no recap for ${route.id}.`);
  const recap = recaps[index];
  const [title, body] = splitTitle(await getText(recap.path));
  const html = markdown(body, "recaps/", route);
  const newer = recaps[index - 1];
  const older = recaps[index + 1];

  const holder = document.createElement("div");
  holder.innerHTML = html;
  const toc = [...holder.querySelectorAll("h2")].map(
    (h) => `<li><a href="#/recap/${esc(recap.week)}?s=${encodeURIComponent(h.id)}">${esc(h.textContent)}</a></li>`,
  );

  document.title = `${title || recap.title} | Colab How-Tos`;
  app.innerHTML = `
    <nav class="crumbs" aria-label="Breadcrumb"><a href="#/">Home</a> <span aria-hidden="true">/</span> <a href="#/?s=recaps">Recaps</a></nav>
    <div class="doc-layout">
      <article class="doc">
        <header class="doc-header">
          <p class="eyebrow">${esc(weekLabel(recap.week))} <span class="dot" aria-hidden="true">·</span> ${esc(dateRange(recap.start, recap.end))}</p>
          <h1 tabindex="-1">${esc(title || recap.title)}</h1>
        </header>
        <div class="prose">${html}</div>
        <footer class="doc-footer">
          <p><a href="${esc(`${repoUrl()}/blob/main/${recap.path}`)}" rel="noopener">View or edit this recap on GitHub</a></p>
          <nav class="pager" aria-label="More recaps">
            ${older ? `<a href="#/recap/${esc(older.week)}"><span class="muted">Older</span> ${esc(older.title)}</a>` : "<span></span>"}
            ${newer ? `<a class="next" href="#/recap/${esc(newer.week)}"><span class="muted">Newer</span> ${esc(newer.title)}</a>` : ""}
          </nav>
        </footer>
      </article>
      ${toc.length ? `<aside class="toc" aria-label="In this recap"><h2 class="small-heading">In this recap</h2><ul>${toc.join("")}</ul></aside>` : ""}
    </div>`;
}

async function renderModule(route) {
  const module = findModule(route.id);
  if (!module) return renderMissing(`There is no module called ${route.id}.`);
  const multi = module.lessons.length > 1;
  const parts = await Promise.all(
    module.lessons.map(async (lesson, n) => {
      if (lesson.type !== "content" || !lesson.path) {
        return `<section class="lesson"><h2>${esc(lesson.title)}</h2><p class="muted">This lesson is a ${esc(lesson.type || "non-text")} lesson. It only runs in the course player.</p></section>`;
      }
      const [, body] = splitTitle(await getText(lesson.path));
      const html = markdown(body, module.path, route, { headingOffset: multi ? 1 : 0 });
      const heading = multi ? `<h2 id="lesson-${esc(lesson.id)}">${n + 1}. ${esc(lesson.title)}</h2>` : "";
      return `<section class="lesson">${heading}<div class="prose">${html}</div></section>`;
    }),
  );

  const recap = module.recap && findRecap(module.recap);
  const facts = [
    `<div><dt>Status</dt><dd>${badge(module.status)} <span class="muted">${esc(STATUS_HELP[module.status] || "")}</span></dd></div>`,
    module.difficulty ? `<div><dt>Difficulty</dt><dd>${esc(module.difficulty)}</dd></div>` : "",
    module.contributors?.length ? `<div><dt>Built by</dt><dd>${esc(listJoin(module.contributors))}</dd></div>` : "",
    recap ? `<div><dt>From</dt><dd><a href="#/recap/${esc(recap.week)}">${esc(recap.title)}</a></dd></div>` : "",
    module.issue
      ? `<div><dt>Issue</dt><dd><a href="${esc(`${repoUrl()}/issues/${module.issue}`)}" rel="noopener">#${esc(module.issue)}</a></dd></div>`
      : "",
  ].join("");
  const lessonNav = multi
    ? `<nav class="lesson-nav" aria-label="Lessons"><ol>${module.lessons
        .map((l) => `<li><a href="#/module/${esc(module.id)}?s=lesson-${encodeURIComponent(l.id)}">${esc(l.title)}</a></li>`)
        .join("")}</ol></nav>`
    : "";

  document.title = `${module.title} | Colab How-Tos`;
  app.innerHTML = `
    <nav class="crumbs" aria-label="Breadcrumb"><a href="#/">Home</a> <span aria-hidden="true">/</span> <a href="#/?s=modules">Modules</a></nav>
    <article class="doc">
      ${module.example ? '<p class="notice">This is the format example for contributors. It is hidden on the home page and never published.</p>' : ""}
      <header class="doc-header">
        <p class="eyebrow">Module</p>
        <h1 tabindex="-1">${esc(module.title)}</h1>
        <p class="lede">${esc(module.description)}</p>
        <dl class="facts">${facts}</dl>
        <ul class="tags" aria-label="Tags">${module.tags.map((t) => `<li><a href="#/?tag=${encodeURIComponent(t)}&s=modules">${esc(t)}</a></li>`).join("")}</ul>
      </header>
      ${lessonNav}
      ${parts.join("")}
      <footer class="doc-footer">
        <p><a href="${esc(`${repoUrl()}/tree/main/${module.path}`)}" rel="noopener">View or edit this module on GitHub</a></p>
      </footer>
    </article>`;
}

function renderMissing(message = "That page doesn't exist.") {
  document.title = "Not found | Colab How-Tos";
  app.innerHTML = `<section class="hero"><h1 tabindex="-1">Not found</h1><p class="lede">${esc(message)}</p>
    <p><a class="button primary" href="#/">Go to the home page</a></p></section>`;
}

function renderError(error) {
  document.title = "Colab How-Tos";
  app.innerHTML = `<section class="hero"><h1 tabindex="-1">Something went wrong</h1>
    <p class="lede">The page couldn't load its content (${esc(error.message)}).</p>
    <p><a class="button" href="${esc(repoUrl())}" rel="noopener">Read it on GitHub instead</a></p></section>`;
}

// --- shell ------------------------------------------------------------------------

function updateNav(route) {
  const section = route.name === "home" ? route.params.get("s") : null;
  document.querySelectorAll("[data-nav]").forEach((a) => {
    if (a.dataset.nav === section) a.setAttribute("aria-current", "location");
    else a.removeAttribute("aria-current");
  });
}

function settle(route) {
  const target = route.params.get("s");
  const el = target && document.getElementById(target);
  if (el) {
    el.scrollIntoView({ block: "start" });
    if (!el.hasAttribute("tabindex")) el.setAttribute("tabindex", "-1");
    el.focus({ preventScroll: true });
  } else {
    window.scrollTo(0, 0);
    // Move focus to the new page heading, but not on first load (it would hide the skip link).
    if (!state.firstRender) app.querySelector("h1")?.focus({ preventScroll: true });
  }
  state.firstRender = false;
}

async function render() {
  const route = parseRoute();
  try {
    if (!state.content) state.content = await getJson("data/content.json");
    if (route.name === "home") await renderHome(route);
    else if (route.name === "recap") await renderRecap(route);
    else if (route.name === "module") await renderModule(route);
    else renderMissing();
  } catch (error) {
    renderError(error);
  }
  updateNav(route);
  settle(route);
}

function wireShell() {
  // Same-page section links (#/?s=...) don't change the hash when already there; scroll anyway.
  document.addEventListener("click", (event) => {
    const link = event.target.closest('a[href^="#/"]');
    if (!link || link.getAttribute("href") !== location.hash) return;
    event.preventDefault();
    settle(parseRoute());
  });
  document.querySelector("[data-skip]")?.addEventListener("click", (event) => {
    event.preventDefault();
    main.focus();
  });
}

window.addEventListener("hashchange", () => {
  // Only "#/..." hashes are routes; ignore anything else.
  if (location.hash === "" || location.hash.startsWith("#/")) render();
});

wireShell();
render().then(() => {
  // Point header and footer links at the repo named in content.json (forks build their own).
  document.querySelectorAll("[data-repo-link]").forEach((a) => {
    const suffix = a.getAttribute("data-repo-link");
    a.href = suffix ? `${repoUrl()}/${suffix}` : repoUrl();
  });
});
