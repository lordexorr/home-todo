"""Home To-Do's lists, and the changes a page sends to them. Nothing here uses Home Assistant, so it can be tested
offline.

Everything is kept in one document:

- lists: "family", shared by everyone, and one list per user, under the user's id.
- categories: the category names every list shares.
- prefs: each user's display settings ("ui") and links ("cfg").
- rev: goes up by one with each change.

A list holds its open tasks ("todos"), its completed log ("done"), its scratchpad ("notes"), and "seq", the next task
number. Task numbers belong to a list, and a task keeps its number when it's completed."""
from __future__ import annotations

import math
import re
import time
from typing import Any

FAMILY = "family"
THEMES = ("slate", "dim", "dark")
SORTS = ("manual", "due", "pri", "age")
LIST_KINDS = ("mine", "family")
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def now_ms() -> int:
    return int(time.time() * 1000)


def _int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return 0
    return 0


def _text(value: Any) -> str:
    if value is None:
        return ""
    return value if isinstance(value, str) else str(value)


def _date(value: Any) -> str:
    return value if isinstance(value, str) and _DATE.fullmatch(value) else ""


def _list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _positive(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0


def norm_ticket(value: Any) -> str:
    return re.sub(r"\s+", "", _text(value).upper())


def category_key(name: str) -> str:
    """What matching compares: "Home Lab", "home_lab" and "homelab" are the same category."""
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def _same_category(a: str, b: str) -> bool:
    ka, kb = category_key(a), category_key(b)
    return ka == kb if ka and kb else a == b


def _add_category(categories: list[str], name: Any) -> bool:
    if not isinstance(name, str) or not name.strip() or any(_same_category(c, name) for c in categories):
        return False
    categories.append(name)
    return True


def norm_subs(value: Any) -> list[dict]:
    """Side tasks. Their numbers only need to be unique within their task. The text is kept exactly as typed, even
    when empty, so a side task being retyped doesn't disappear while someone's typing it."""
    seen: set[int] = set()
    out: list[dict] = []
    for x in _list(value):
        if not isinstance(x, dict):
            continue
        sid = _int(x.get("id"))
        if sid < 1 or sid in seen:
            sid = 0
        out.append({"id": sid, "text": _text(x.get("text")), "done": bool(x.get("done")),
                    "notes": _text(x.get("notes"))})
        if sid:
            seen.add(sid)
    nxt = max(seen, default=0) + 1
    for sb in out:
        if not sb["id"]:
            sb["id"] = nxt
            nxt += 1
    return out


def norm_todo(t: Any, now: int) -> dict:
    """An open task, with every field present and valid."""
    t = _dict(t)
    created = _int(t.get("created")) or now
    return {
        "id": _int(t.get("id")),
        "text": _text(t.get("text")),
        "category": _text(t.get("category")) or None,
        "pri": t.get("pri") if t.get("pri") in ("hi", "lo") else "md",
        "status": "waiting" if t.get("status") == "waiting" else "open",
        "waitingOn": _text(t.get("waitingOn")),
        "followUp": _date(t.get("followUp")),
        "due": _date(t.get("due")),
        "ticket": norm_ticket(t.get("ticket")),
        "subs": norm_subs(t.get("subs")),
        "subsOpen": bool(t.get("subsOpen")),
        "notes": _text(t.get("notes")),
        "created": created,
        "updated": _int(t.get("updated")) or created,
    }


def norm_done(e: Any, now: int) -> dict:
    """An entry in the completed log."""
    e = _dict(e)
    return {
        "id": _int(e.get("id")),
        "text": _text(e.get("text")),
        "category": _text(e.get("category")) or None,
        "ts": _int(e.get("ts")) or now,
        "ticket": norm_ticket(e.get("ticket")),
        "subs": norm_subs(e.get("subs")),
        "notes": _text(e.get("notes")),
    }


def new_list(list_id: str) -> dict:
    return {"id": list_id, "seq": 1, "todos": [], "done": [], "notes": ""}


def norm_list(raw: Any, list_id: str, now: int) -> dict:
    raw = _dict(raw)
    todos = [norm_todo(t, now) for t in _list(raw.get("todos")) if isinstance(t, dict)]
    done = [norm_done(e, now) for e in _list(raw.get("done")) if isinstance(e, dict)]
    top = max((x["id"] for x in todos + done), default=0)
    seen: set[int] = set()
    for item in todos + done:  # every task number is used once in its list
        if item["id"] < 1 or item["id"] in seen:
            top += 1
            item["id"] = top
        seen.add(item["id"])
    return {"id": list_id, "seq": max(_int(raw.get("seq")), top + 1), "todos": todos, "done": done,
            "notes": _text(raw.get("notes"))}


def norm_prefs(raw: Any) -> dict:
    """A user's display settings and links, keeping only values the page can use."""
    raw = _dict(raw)
    ui_in, cfg_in = _dict(raw.get("ui")), _dict(raw.get("cfg"))
    ui: dict[str, Any] = {}
    cols = ui_in.get("cols")
    if isinstance(cols, list) and len(cols) == 3 and all(_positive(n) for n in cols):
        ui["cols"] = cols
    collapsed = ui_in.get("collapsed")
    if isinstance(collapsed, list) and len(collapsed) == 3:
        ui["collapsed"] = [bool(c) for c in collapsed]
    if ui_in.get("sort") in SORTS:
        ui["sort"] = ui_in["sort"]
    if isinstance(ui_in.get("showTime"), bool):
        ui["showTime"] = ui_in["showTime"]
    if ui_in.get("theme") in THEMES and ui_in.get("themePick") is True:  # only a theme the user chose
        ui["theme"] = ui_in["theme"]
        ui["themePick"] = True
    if ui_in.get("list") in LIST_KINDS:
        ui["list"] = ui_in["list"]
    cfg: dict[str, Any] = {}
    if isinstance(cfg_in.get("snow"), str):
        cfg["snow"] = cfg_in["snow"].strip()
    if isinstance(cfg_in.get("links"), list):
        cfg["links"] = [{"label": link["label"].strip(), "path": link["path"].strip()}
                        for link in cfg_in["links"]
                        if isinstance(link, dict) and isinstance(link.get("label"), str)
                        and isinstance(link.get("path"), str) and link["label"].strip() and link["path"].strip()]
    return {"ui": ui, "cfg": cfg}


def new_doc() -> dict:
    return {"rev": 0, "lists": {FAMILY: new_list(FAMILY)}, "categories": [], "prefs": {}}


def norm_doc(raw: Any) -> dict:
    """What was saved, made safe to use: anything missing or malformed is left out or set to its default."""
    raw = _dict(raw)
    now = now_ms()
    lists = {lid: norm_list(lst, lid, now) for lid, lst in _dict(raw.get("lists")).items()
             if isinstance(lid, str) and lid}
    lists.setdefault(FAMILY, new_list(FAMILY))
    categories: list[str] = []
    for name in _list(raw.get("categories")):
        _add_category(categories, name)
    prefs = {uid: norm_prefs(p) for uid, p in _dict(raw.get("prefs")).items() if isinstance(uid, str)}
    return {"rev": max(_int(raw.get("rev")), 0), "lists": lists, "categories": categories, "prefs": prefs}


def ensure_personal(doc: dict, user_id: str) -> bool:
    """Makes the user's own list the first time they open Home To-Do. True if it was made."""
    if user_id in doc["lists"]:
        return False
    doc["lists"][user_id] = new_list(user_id)
    return True


def _ordered(items: list[dict], ids: list[int]) -> list[dict]:
    """items in the order a page sent. Anything the page didn't know about, because someone else added it a moment
    ago, stays just after the item it followed."""
    pos: dict[int, int] = {}
    for i, item_id in enumerate(ids):
        pos.setdefault(item_id, i)
    keyed = []
    last = -1
    for index, item in enumerate(items):
        if item["id"] in pos:
            last = pos[item["id"]]
            keyed.append((last, 0, index, item))
        else:
            keyed.append((last, 1, index, item))
    keyed.sort(key=lambda k: k[:3])
    return [k[3] for k in keyed]


def apply_changes(doc: dict, list_id: str, changes: Any, now: int | None = None) -> dict[str, dict[str, int]]:
    """Applies what a page changed in one list. Each task is changed on its own, so edits made on two pages at once
    both stay. A change to a task someone else has since deleted or completed is dropped.

    Returns the task numbers that had to change: when two pages add a task with the same number at once, the second
    one gets the list's next number."""
    now = now or now_ms()
    lst = doc["lists"][list_id]
    changes = _dict(changes)
    parts = {key: _dict(changes.get(key)) for key in ("todos", "done")}
    for key, part in parts.items():
        gone = {_int(i) for i in _list(part.get("remove"))}
        if gone:
            lst[key] = [x for x in lst[key] if x["id"] not in gone]
    remap: dict[str, dict[int, int]] = {"todos": {}, "done": {}}
    for key, norm in (("todos", norm_todo), ("done", norm_done)):
        part, items = parts[key], lst[key]
        where = {x["id"]: i for i, x in enumerate(items)}
        for raw in _list(part.get("update")):
            if isinstance(raw, dict):
                item = norm(raw, now)
                if item["id"] in where:
                    items[where[item["id"]]] = item
        for raw in _list(part.get("add")):
            if not isinstance(raw, dict):
                continue
            item = norm(raw, now)
            if item["id"] in where and items[where[item["id"]]] == item:
                continue  # sent again after a dropped connection, and already here
            taken = {x["id"] for x in lst["todos"]} | {x["id"] for x in lst["done"]}
            if item["id"] < 1 or item["id"] in taken:
                old = item["id"]
                item["id"] = max(lst["seq"], max(taken, default=0) + 1)
                remap[key][old] = item["id"]
            where[item["id"]] = len(items)
            items.append(item)
            lst["seq"] = max(lst["seq"], item["id"] + 1)
        if isinstance(part.get("order"), list):
            lst[key] = _ordered(items, [remap[key].get(_int(i), _int(i)) for i in part["order"]])
    if isinstance(changes.get("notes"), str):
        lst["notes"] = changes["notes"]
    cats = _dict(changes.get("categories"))
    for name in _list(cats.get("remove")):
        doc["categories"] = [c for c in doc["categories"] if c != name]
    for name in _list(cats.get("add")):
        _add_category(doc["categories"], name)
    return {key: {str(old): new for old, new in m.items()} for key, m in remap.items() if m}
