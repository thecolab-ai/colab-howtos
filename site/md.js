// Small markdown renderer for the Colab how-tos viewer. MIT licence, written for this repo.
//
// Covers what the recaps and modules use: ATX headings, paragraphs, nested ordered and
// unordered lists, fenced code, block quotes, GFM tables, rules, and inline code, links,
// images, autolinks, bold, italic and strikethrough. Raw HTML is always escaped, and link
// targets are limited to http(s), mailto, relative paths and in-page anchors.
//
// renderMarkdown(source, options) returns an HTML string. Options:
//   link(href)        -> href to use for a link (default: unchanged)
//   image(src)        -> src to use for an image (default: unchanged)
//   inline            -> [{ re: /global regex/, html(match) -> string }] extra inline rules
//   headingId(text)   -> id for a heading (default: slugify, de-duplicated per document)
//   headingOffset     -> add this to every heading level, capped at 6 (default 0)

const ESCAPES = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };

export function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (c) => ESCAPES[c]);
}

export function slugify(text) {
  return String(text)
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9\s-]/g, "")
    .trim()
    .replace(/[\s-]+/g, "-");
}

export function safeUrl(raw) {
  const url = String(raw).trim().replace(/[\u0000-\u001f\u007f\s]+/g, "");
  const scheme = /^([a-z][a-z0-9+.-]*):/i.exec(url);
  if (scheme && !["http", "https", "mailto"].includes(scheme[1].toLowerCase())) return "#";
  return url;
}

const RULE_RE = /^ {0,3}([-*_])(?:[ \t]*\1){2,}[ \t]*$/;
const HEADING_RE = /^ {0,3}(#{1,6})(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*$/;
const FENCE_RE = /^( {0,3})(`{3,}|~{3,})[ \t]*([^`]*)$/;
const LIST_RE = /^( {0,3})([-*+]|\d{1,9}[.)])([ \t]+|$)(.*)$/;
const QUOTE_RE = /^ {0,3}> ?(.*)$/;
const TABLE_SEP_RE = /^ {0,3}\|?[ \t]*:?-+:?[ \t]*(?:\|[ \t]*:?-+:?[ \t]*)*\|?[ \t]*$/;

function isBlank(line) {
  return /^[ \t]*$/.test(line);
}

function startsBlock(line) {
  return (
    HEADING_RE.test(line) || FENCE_RE.test(line) || RULE_RE.test(line) || QUOTE_RE.test(line) || LIST_RE.test(line)
  );
}

function splitRow(line) {
  let row = line.trim();
  if (row.startsWith("|")) row = row.slice(1);
  if (row.endsWith("|") && !row.endsWith("\\|")) row = row.slice(0, -1);
  const cells = [];
  let current = "";
  let inCode = false;
  for (let i = 0; i < row.length; i += 1) {
    const ch = row[i];
    if (ch === "\\" && row[i + 1] === "|") {
      current += "|";
      i += 1;
    } else if (ch === "`") {
      inCode = !inCode;
      current += ch;
    } else if (ch === "|" && !inCode) {
      cells.push(current.trim());
      current = "";
    } else {
      current += ch;
    }
  }
  cells.push(current.trim());
  return cells;
}

function dedent(lines, width) {
  return lines.map((line) => {
    let n = 0;
    while (n < width && line[n] === " ") n += 1;
    return line.slice(n);
  });
}

class Renderer {
  constructor(options = {}) {
    this.link = options.link || ((href) => href);
    this.image = options.image || ((src) => src);
    this.extra = options.inline || [];
    this.headingOffset = options.headingOffset || 0;
    this.usedIds = new Map();
    this.headingId =
      options.headingId ||
      ((text) => {
        const base = slugify(text) || "section";
        const seen = this.usedIds.get(base) || 0;
        this.usedIds.set(base, seen + 1);
        return seen ? `${base}-${seen}` : base;
      });
  }

  // --- blocks -------------------------------------------------------------------

  blocks(lines, tight = false) {
    const out = [];
    let i = 0;
    while (i < lines.length) {
      const line = lines[i];
      if (isBlank(line)) {
        i += 1;
        continue;
      }

      const fence = FENCE_RE.exec(line);
      if (fence) {
        const [, indent, marker, info] = fence;
        const body = [];
        i += 1;
        while (i < lines.length && !new RegExp(`^ {0,3}${marker[0]}{${marker.length},}[ \\t]*$`).test(lines[i])) {
          body.push(lines[i]);
          i += 1;
        }
        i += 1;
        const lang = info.trim().split(/\s+/)[0];
        const cls = lang ? ` class="language-${escapeHtml(lang)}"` : "";
        const code = dedent(body, indent.length).join("\n");
        out.push(`<pre><code${cls}>${escapeHtml(code)}${code ? "\n" : ""}</code></pre>`);
        continue;
      }

      const heading = HEADING_RE.exec(line);
      if (heading) {
        const level = Math.min(6, heading[1].length + this.headingOffset);
        const text = (heading[2] || "").trim();
        const id = this.headingId(text.replace(/[*_`]/g, ""), level);
        out.push(`<h${level} id="${escapeHtml(id)}">${this.inline(text)}</h${level}>`);
        i += 1;
        continue;
      }

      if (RULE_RE.test(line)) {
        out.push("<hr>");
        i += 1;
        continue;
      }

      if (QUOTE_RE.test(line)) {
        const body = [];
        while (i < lines.length && !isBlank(lines[i])) {
          const quote = QUOTE_RE.exec(lines[i]);
          body.push(quote ? quote[1] : lines[i]);
          i += 1;
        }
        out.push(`<blockquote>\n${this.blocks(body)}\n</blockquote>`);
        continue;
      }

      if (LIST_RE.test(line)) {
        i = this.list(lines, i, out);
        continue;
      }

      if (line.includes("|") && i + 1 < lines.length && TABLE_SEP_RE.test(lines[i + 1]) && lines[i + 1].includes("-")) {
        i = this.table(lines, i, out);
        continue;
      }

      const para = [];
      while (i < lines.length && !isBlank(lines[i]) && (para.length === 0 || !startsBlock(lines[i]))) {
        para.push(lines[i]);
        i += 1;
      }
      const html = para
        .map((l, n) => {
          const last = n === para.length - 1;
          const hard = !last && (/ {2,}$/.test(l) || /\\$/.test(l));
          const text = this.inline(l.trim().replace(/\\$/, ""));
          return hard ? `${text}<br>` : text;
        })
        .join("\n");
      out.push(tight ? html : `<p>${html}</p>`);
    }
    return out.join("\n");
  }

  list(lines, start, out) {
    const first = LIST_RE.exec(lines[start]);
    const ordered = /\d/.test(first[2]);
    const delimiter = first[2].slice(-1);
    const items = [];
    let loose = false;
    let i = start;

    while (i < lines.length) {
      const match = LIST_RE.exec(lines[i]);
      if (!match || /\d/.test(match[2]) !== ordered || match[2].slice(-1) !== delimiter) break;
      const width = match[1].length + match[2].length + Math.min(match[3].length || 1, 4);
      const body = [match[4]];
      i += 1;
      let sawBlank = false;
      while (i < lines.length) {
        const next = lines[i];
        if (isBlank(next)) {
          sawBlank = true;
          body.push("");
          i += 1;
          continue;
        }
        const indent = next.length - next.trimStart().length;
        if (indent >= width) {
          if (sawBlank && body.some((l) => l.trim())) loose = loose || !LIST_RE.test(next.slice(width));
          body.push(next.slice(width));
          sawBlank = false;
          i += 1;
          continue;
        }
        if (!sawBlank && !startsBlock(next)) {
          body.push(next.trim()); // lazy paragraph continuation
          i += 1;
          continue;
        }
        break;
      }
      while (body.length && isBlank(body[body.length - 1])) body.pop();
      if (sawBlank && i < lines.length && LIST_RE.test(lines[i])) {
        const next = LIST_RE.exec(lines[i]);
        if (/\d/.test(next[2]) === ordered && next[2].slice(-1) === delimiter) loose = true;
      }
      items.push(body);
    }

    const tag = ordered ? "ol" : "ul";
    const startNumber = ordered ? parseInt(first[2], 10) : 1;
    const startAttr = ordered && startNumber !== 1 ? ` start="${startNumber}"` : "";
    const lis = items.map((body) => `<li>${this.blocks(body, !loose)}</li>`);
    out.push(`<${tag}${startAttr}>\n${lis.join("\n")}\n</${tag}>`);
    return i;
  }

  table(lines, start, out) {
    const header = splitRow(lines[start]);
    const aligns = splitRow(lines[start + 1]).map((c) => {
      const left = c.startsWith(":");
      const right = c.endsWith(":");
      if (left && right) return "center";
      if (right) return "right";
      if (left) return "left";
      return "";
    });
    const cell = (tag, text, n) => {
      const align = aligns[n] ? ` style="text-align:${aligns[n]}"` : "";
      return `<${tag}${align}>${this.inline(text || "")}</${tag}>`;
    };
    let i = start + 2;
    const rows = [];
    while (i < lines.length && !isBlank(lines[i]) && lines[i].includes("|")) {
      const cells = splitRow(lines[i]);
      rows.push(`<tr>${header.map((_, n) => cell("td", cells[n], n)).join("")}</tr>`);
      i += 1;
    }
    out.push(
      `<div class="table-wrap"><table>\n<thead><tr>${header.map((h, n) => cell("th", h, n)).join("")}</tr></thead>\n` +
        `<tbody>\n${rows.join("\n")}\n</tbody>\n</table></div>`,
    );
    return i;
  }

  // --- inline -------------------------------------------------------------------

  inline(text) {
    const stash = [];
    const keep = (html) => `\u0000${stash.push(html) - 1}\u0000`;
    let s = String(text).replace(/\u0000/g, "");

    // Code spans first, so nothing inside them is touched.
    s = s.replace(/(`+)([\s\S]*?[^`])\1(?!`)/g, (_, __, code) => keep(`<code>${escapeHtml(code.trim())}</code>`));
    // Backslash escapes.
    s = s.replace(/\\([\\`*_{}[\]()#+\-.!|~<>])/g, (_, ch) => keep(escapeHtml(ch)));
    for (const rule of this.extra) s = s.replace(rule.re, (...m) => keep(rule.html(m)));
    // Images, then links. Link text may hold inline formatting but not other links.
    s = s.replace(/!\[([^\]]*)\]\(\s*<?((?:[^()\s<>]|\([^()\s<>]*\))+)>?(?:\s+"([^"]*)")?\s*\)/g, (_, alt, src, title) => {
      const t = title ? ` title="${escapeHtml(title)}"` : "";
      return keep(`<img src="${escapeHtml(safeUrl(this.image(src)))}" alt="${escapeHtml(alt)}" loading="lazy"${t}>`);
    });
    s = s.replace(/\[((?:[^\[\]]|\[[^\]]*\])+)\]\(\s*<?((?:[^()\s<>]|\([^()\s<>]*\))+)>?(?:\s+"([^"]*)")?\s*\)/g, (_, label, href, title) =>
      keep(this.anchor(href, this.emphasis(escapeHtml(label), stash), title)),
    );
    s = s.replace(/<((?:https?:\/\/|mailto:)[^\s<>]+)>/g, (_, url) => keep(this.anchor(url, escapeHtml(url))));
    s = s.replace(/\bhttps?:\/\/[^\s<>\u0000]*[^\s<>\u0000.,:;"')\]!?]/g, (url) => keep(this.anchor(url, escapeHtml(url))));

    s = this.emphasis(escapeHtml(s), stash);
    // Restore stashed fragments (they may nest, so loop until none are left).
    for (let n = 0; n < 5 && s.includes("\u0000"); n += 1) {
      s = s.replace(/\u0000(\d+)\u0000/g, (_, k) => stash[Number(k)]);
    }
    return s;
  }

  emphasis(s) {
    return s
      .replace(/\*\*(?=\S)([\s\S]*?\S)\*\*/g, "<strong>$1</strong>")
      .replace(/(^|[^\w])__(?=\S)([\s\S]*?\S)__(?!\w)/g, "$1<strong>$2</strong>")
      .replace(/\*(?=[^\s*])([^*]*?[^\s*])\*/g, "<em>$1</em>")
      .replace(/\*([^\s*])\*/g, "<em>$1</em>")
      .replace(/(^|[^\w])_(?=[^\s_])([^_]*?[^\s_]|[^\s_])_(?!\w)/g, "$1<em>$2</em>")
      .replace(/~~(?=\S)([\s\S]*?\S)~~/g, "<del>$1</del>");
  }

  anchor(href, labelHtml, title) {
    const target = safeUrl(this.link(href));
    const external = /^https?:\/\//i.test(target);
    const rel = external ? ' rel="noopener"' : "";
    const t = title ? ` title="${escapeHtml(title)}"` : "";
    return `<a href="${escapeHtml(target)}"${rel}${t}>${labelHtml}</a>`;
  }
}

export function renderMarkdown(source, options = {}) {
  const lines = String(source).replace(/\r\n?/g, "\n").replace(/\t/g, "    ").split("\n");
  return new Renderer(options).blocks(lines);
}
