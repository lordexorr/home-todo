// Home To-Do's page in the sidebar. Home Assistant runs it in a frame of its own (embed_iframe), so the page keeps
// its own styles and keyboard shortcuts. This loads home-todo.html into that frame, and adds the menu button that
// opens Home Assistant's sidebar when it's hidden, as on a phone.

const VERSION = new URL(import.meta.url).search; // ?v=…, so an update is fetched afresh
const PAGE = new URL("home-todo.html" + VERSION, import.meta.url);
const MENU_ICON =
  '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" ' +
  'aria-hidden="true"><path d="M2.5 4h11M2.5 8h11M2.5 12h11"/></svg>';

class HomeTodoPanel extends HTMLElement {
  constructor() {
    super();
    this._hass = null;
    this._narrow = false;
    this._menu = null;
    this._started = false;
  }

  get hass() { return this._hass; }
  set hass(hass) {
    this._hass = hass;
    this._showMenu();
    if (this.onHass) this.onHass(hass); // the page follows Home Assistant's light/dark setting
  }
  set narrow(narrow) { this._narrow = Boolean(narrow); this._showMenu(); }
  set panel(panel) { this._panel = panel; }
  set route(route) { this._route = route; }

  connectedCallback() {
    if (this._started) return;
    this._started = true;
    this.style.display = "contents"; // the page's markup lays out as if it were the frame's body
    this._load().catch((err) => this._fail(err));
  }

  async _load() {
    const res = await fetch(PAGE, { cache: "no-cache" });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    const page = new DOMParser().parseFromString(await res.text(), "text/html");
    for (const attr of page.documentElement.attributes) document.documentElement.setAttribute(attr.name, attr.value);
    document.title = page.title;
    // Styles and scripts go in in the page's order. A parsed script doesn't run until it's recreated.
    for (const node of page.head.children) {
      if (node.tagName === "STYLE") document.head.appendChild(document.importNode(node, true));
      else if (node.tagName === "SCRIPT") runScript(node, document.head);
    }
    const scripts = [];
    for (const node of Array.from(page.body.childNodes)) {
      if (node.nodeName === "SCRIPT") scripts.push(node);
      else this.appendChild(document.importNode(node, true));
    }
    this._addMenu();
    window.homeTodoHost = this; // the page reaches Home Assistant's connection through this.hass
    for (const node of scripts) runScript(node, this);
  }

  _addMenu() {
    const bar = this.querySelector(".topbar");
    if (!bar) return;
    const btn = document.createElement("button");
    btn.className = "themebtn";
    btn.title = "Home Assistant menu";
    btn.setAttribute("aria-label", "Open Home Assistant's sidebar");
    btn.innerHTML = MENU_ICON;
    btn.addEventListener("click", () => {
      this.dispatchEvent(new CustomEvent("hass-toggle-menu", { bubbles: true, composed: true }));
    });
    bar.insertBefore(btn, bar.firstChild);
    this._menu = btn;
    this._showMenu();
  }

  // Home Assistant's own pages show this button when the sidebar is hidden: on a narrow screen, or when the user
  // has chosen to always hide it.
  _showMenu() {
    if (!this._menu) return;
    const alwaysHidden = Boolean(this._hass && this._hass.dockedSidebar === "always_hidden");
    this._menu.hidden = !(this._narrow || alwaysHidden);
  }

  _fail(err) {
    const box = document.createElement("div");
    box.style.cssText = "padding:24px;font:14px system-ui,sans-serif";
    box.textContent = "Home To-Do's page couldn't load: " + (err && err.message ? err.message : String(err));
    this.style.display = "";
    this.replaceChildren(box);
  }
}

function runScript(node, parent) {
  const script = document.createElement("script");
  for (const attr of node.attributes) script.setAttribute(attr.name, attr.value);
  script.textContent = node.textContent;
  parent.appendChild(script);
}

if (!customElements.get("home-todo-panel")) customElements.define("home-todo-panel", HomeTodoPanel);
