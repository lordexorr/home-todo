"""Home To-Do's lists, and the changes a page sends to them. Nothing here uses Home Assistant, so it can be tested
offline.

Everything is kept in one document:

- lists: "family", shared by everyone, and one list per user, under the user's id.
- prefs: each user's display settings ("ui"), and their top-bar shortcuts and whether their list is on Home
  Assistant's calendar ("cfg").
- rev: goes up by one with each change.

A list holds its open tasks ("todos"), its completed log ("done"), log entries more than a year old ("archive"), its
scratchpad ("notes"), its category names ("categories"), and "seq", the next task number. Family's categories are shared, and a personal list's are its owner's
alone. Task numbers belong to a list, and a task keeps its number when it's completed.

A Family task can be for someone ("for", a user id): a request. "forBy" is whoever made it for them, as Home
Assistant saw it, never as a page says. A log entry keeps both, and "from", the task it was ticked off from.

A task can be linked to one area ("area", an area id) or one device ("device", a device id) in Home Assistant.

A task can repeat. Ticked off, it goes to the log under a new number and stays open with its next due date. "from"
says what that's counted from: "due", on a schedule from its due date, or "done", from the day it was ticked off."""
from __future__ import annotations

import difflib
import math
import re
import time
from calendar import monthrange
from datetime import date, timedelta
from typing import Any

FAMILY = "family"
SORTS = ("manual", "due", "pri", "cat", "age")  # what tasks are sorted by first
THEN_SORTS = ("none", "due", "pri", "cat", "age")  # and then by
LIST_KINDS = ("mine", "family")
REPEAT_UNITS = ("day", "week", "month", "year")
REPEAT_MAX = 999  # the most days, weeks, months or years between repeats
PRI_NAMES = {"hi": "High", "md": "Medium", "lo": "Low"}
ARCHIVE_AFTER_MS = 365 * 24 * 3600 * 1000  # log entries older than this move to the archive
TAIL = 20  # how many of the log's last entry numbers a page is sent, to check its copy is in step
SAME_TICK_MS = 30_000  # a task ticked off on two pages this close together is logged once
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


def norm_repeat(value: Any) -> dict | None:
    """How often a task repeats, or None. "day" is the day of the month a monthly or yearly schedule keeps to, so
    one due on the 31st is due on the last day of shorter months and back on the 31st after them."""
    value = _dict(value)
    every = _int(value.get("every"))
    if every < 1 or value.get("unit") not in REPEAT_UNITS:
        return None
    out: dict[str, Any] = {"every": min(every, REPEAT_MAX), "unit": value["unit"],
                           "from": "done" if value.get("from") == "done" else "due"}
    day = _int(value.get("day"))
    if 1 <= day <= 31:
        out["day"] = day
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
        "subs": norm_subs(t.get("subs")),
        "subsOpen": bool(t.get("subsOpen")),
        "notes": _text(t.get("notes")),
        "repeat": norm_repeat(t.get("repeat")),
        "for": _text(t.get("for")),
        "forBy": _text(t.get("forBy")),
        "area": _text(t.get("area")),
        "device": _text(t.get("device")),
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
        "subs": norm_subs(e.get("subs")),
        "notes": _text(e.get("notes")),
        "from": _int(e.get("from")),
        "for": _text(e.get("for")),
        "forBy": _text(e.get("forBy")),
        "area": _text(e.get("area")),
        "device": _text(e.get("device")),
    }


def new_list(list_id: str) -> dict:
    return {"id": list_id, "seq": 1, "todos": [], "done": [], "archive": [], "notes": "", "categories": []}


def norm_list(raw: Any, list_id: str, now: int) -> dict:
    raw = _dict(raw)
    todos = [norm_todo(t, now) for t in _list(raw.get("todos")) if isinstance(t, dict)]
    done = [norm_done(e, now) for e in _list(raw.get("done")) if isinstance(e, dict)]
    archive = [norm_done(e, now) for e in _list(raw.get("archive")) if isinstance(e, dict)]
    top = max((x["id"] for x in todos + done + archive), default=0)
    seen: set[int] = set()
    for item in todos + done + archive:  # every task number is used once in its list
        if item["id"] < 1 or item["id"] in seen:
            top += 1
            item["id"] = top
        seen.add(item["id"])
    categories: list[str] = []
    for name in _list(raw.get("categories")):
        _add_category(categories, name)
    return {"id": list_id, "seq": max(_int(raw.get("seq")), top + 1), "todos": todos, "done": done,
            "archive": archive, "notes": _text(raw.get("notes")), "categories": categories}


def norm_prefs(raw: Any) -> dict:
    """A user's display settings, top-bar shortcuts and calendar setting, keeping only values the page can use."""
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
    if ui_in.get("sort2") in THEN_SORTS:
        ui["sort2"] = ui_in["sort2"]
    if isinstance(ui_in.get("showTime"), bool):
        ui["showTime"] = ui_in["showTime"]
    if ui_in.get("list") in LIST_KINDS:
        ui["list"] = ui_in["list"]
    cfg: dict[str, Any] = {}
    if isinstance(cfg_in.get("calendar"), bool):
        cfg["calendar"] = cfg_in["calendar"]
    if isinstance(cfg_in.get("notify"), str) and re.fullmatch(r"notify\.[a-z0-9_]+", cfg_in["notify"]):
        cfg["notify"] = cfg_in["notify"]  # where this person's request notifications go
    if isinstance(cfg_in.get("linksSaved"), bool):  # once saved, no links means they removed the example
        cfg["linksSaved"] = cfg_in["linksSaved"]
    if isinstance(cfg_in.get("links"), list):
        cfg["links"] = [{"label": link["label"].strip(), "path": link["path"].strip()}
                        for link in cfg_in["links"]
                        if isinstance(link, dict) and isinstance(link.get("label"), str)
                        and isinstance(link.get("path"), str) and link["label"].strip() and link["path"].strip()]
    return {"ui": ui, "cfg": cfg}


def new_doc() -> dict:
    return {"rev": 0, "lists": {FAMILY: new_list(FAMILY)}, "prefs": {}}


def _share_out(names: list[str], lists: dict[str, dict]) -> None:
    """Categories from before each list had its own: each goes to the lists with a task or log entry in it, and one
    that nothing uses goes to Family."""
    for name in names:
        using = [lst for lst in lists.values()
                 if any(_same_category(x["category"] or "", name) for x in lst["todos"] + lst["done"])]
        for lst in using or [lists[FAMILY]]:
            _add_category(lst["categories"], name)


def norm_doc(raw: Any) -> dict:
    """What was saved, made safe to use: anything missing or malformed is left out or set to its default."""
    raw = _dict(raw)
    now = now_ms()
    lists = {lid: norm_list(lst, lid, now) for lid, lst in _dict(raw.get("lists")).items()
             if isinstance(lid, str) and lid}
    lists.setdefault(FAMILY, new_list(FAMILY))
    shared: list[str] = []
    for name in _list(raw.get("categories")):
        _add_category(shared, name)
    _share_out(shared, lists)
    prefs = {uid: norm_prefs(p) for uid, p in _dict(raw.get("prefs")).items() if isinstance(uid, str)}
    return {"rev": max(_int(raw.get("rev")), 0), "lists": lists, "prefs": prefs}


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


def _assign(item: dict, current: dict | None, user_id: str) -> None:
    """Who asked: the person whose change made the task for someone, whatever the page sent."""
    if current is not None and item["for"] == current["for"]:
        item["forBy"] = current["forBy"]
    else:
        item["forBy"] = user_id if item["for"] else ""


def apply_changes(doc: dict, list_id: str, changes: Any, now: int | None = None,
                  user_id: str = "") -> dict[str, dict[str, int]]:
    """Applies what a page changed in one list. Each task is changed on its own, so edits made on two pages at once
    both stay. A change to a task someone else has since deleted or completed is dropped.

    Returns the task numbers that had to change: when two pages add a task with the same number at once, the second
    one gets the list's next number.

    A field an edit leaves out keeps what it was, so a page from before the field existed doesn't erase it. Notes
    sent with "notesBase", the notes the page started from, are merged with any change someone else made meanwhile.
    user_id is who made the change: it's recorded as who asked, for a task made for someone."""
    now = now or now_ms()
    lst = doc["lists"][list_id]
    changes = _dict(changes)
    parts = {key: _dict(changes.get(key)) for key in ("todos", "done")}
    tasks_before = {x["id"]: x for x in lst["todos"]}  # a log entry takes who it was for from its task
    for key, part in parts.items():
        gone = {_int(i) for i in _list(part.get("remove"))}
        if gone:
            lst[key] = [x for x in lst[key] if x["id"] not in gone]
    remap: dict[str, dict[int, int]] = {"todos": {}, "done": {}}
    for key, norm in (("todos", norm_todo), ("done", norm_done)):
        part, items = parts[key], lst[key]
        where = {x["id"]: i for i, x in enumerate(items)}
        for raw in _list(part.get("update")):
            if isinstance(raw, dict) and (item_id := _int(raw.get("id"))) in where:
                current = items[where[item_id]]
                item = norm({**current, **raw}, now)
                if isinstance(raw.get("notesBase"), str) and isinstance(raw.get("notes"), str):
                    item["notes"] = merge_text(raw["notesBase"], raw["notes"], current["notes"])
                if key == "todos":
                    _assign(item, current, user_id)
                else:
                    item["from"], item["for"], item["forBy"] = current["from"], current["for"], current["forBy"]
                items[where[item_id]] = item
        for raw in _list(part.get("add")):
            if not isinstance(raw, dict):
                continue
            item = norm(raw, now)
            if key == "todos":
                _assign(item, None, user_id)
            else:
                source = tasks_before.get(item["from"] or item["id"])
                item["for"], item["forBy"] = (source["for"], source["forBy"]) if source else ("", "")
                if item["from"] and any(e["from"] == item["from"] and abs(e["ts"] - item["ts"]) < SAME_TICK_MS
                                        for e in items):
                    continue  # ticked off on another page at the same moment, or sent again: logged once
            if item["id"] in where and items[where[item["id"]]] == item:
                continue  # sent again after a dropped connection, and already here
            taken = {x["id"] for x in lst["todos"] + lst["done"] + lst["archive"]}
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
        base = changes.get("notesBase")
        lst["notes"] = merge_text(base, changes["notes"], lst["notes"]) if isinstance(base, str) else changes["notes"]
    cats = _dict(changes.get("categories"))
    for name in _list(cats.get("remove")):
        lst["categories"] = [c for c in lst["categories"] if c != name]
    for name in _list(cats.get("add")):
        _add_category(lst["categories"], name)
    return {key: {str(old): new for old, new in m.items()} for key, m in remap.items() if m}


# ---------- repeating tasks, and the calendar ----------

def parse_date(value: Any) -> date | None:
    try:
        return date.fromisoformat(value) if _date(value) else None
    except ValueError:
        return None


def repeat_step(base: date, rep: dict, times: int) -> date:
    """base moved on by the repeat's interval, so many times over. Months and years keep to the repeat's day of the
    month where it has one, and otherwise to base's, falling on the last day of shorter months."""
    n = rep["every"] * times
    if rep["unit"] == "day":
        return base + timedelta(days=n)
    if rep["unit"] == "week":
        return base + timedelta(weeks=n)
    if rep["unit"] == "month":
        months = base.month - 1 + n
        year, month = base.year + months // 12, months % 12 + 1
    else:
        year, month = base.year + n, base.month
    return date(year, month, min(rep.get("day") or base.day, monthrange(year, month)[1]))


def _first_step(due: date, rep: dict, after: date) -> int:
    """A number of steps from due that's no later than the first one past after, so counting starts near it."""
    gap = (after - due).days
    if gap <= 0:
        return 1
    per = {"day": 1, "week": 7, "month": 31, "year": 366}[rep["unit"]] * rep["every"]
    return max(1, gap // per)


def next_due(todo: dict, today: date) -> date:
    """The due date a repeating task moves to when it's ticked off today. On a schedule, that's the first date in it
    after today, so missed ones don't pile up. After it's done, it's counted from today."""
    rep, due = todo["repeat"], parse_date(todo.get("due"))
    if rep["from"] == "done" or not due:
        return repeat_step(today, {**rep, "day": None}, 1)
    times = _first_step(due, rep, today)
    while (day := repeat_step(due, rep, times)) <= today:
        times += 1
    return day


def task_days(todo: dict, first: date, last: date, today: date) -> list[date]:
    """The days from first to last a task is on the calendar: its due date and, if it repeats on a schedule, every
    date after today that it'll be due on."""
    due = parse_date(todo.get("due"))
    if not due:
        return []
    days = [due] if first <= due <= last else []
    rep = todo.get("repeat")
    if not rep or rep["from"] != "due":
        return days
    times = _first_step(due, rep, max(first, today))
    while times < 100_000:
        try:
            day = repeat_step(due, rep, times)
        except (OverflowError, ValueError):  # past the year 9999
            break
        if day > last:
            break
        if day > today and day >= first:
            days.append(day)
        times += 1
    return days


def next_day(todo: dict, today: date) -> date | None:
    """The first day, today or later, a task is on the calendar."""
    due = parse_date(todo.get("due"))
    if not due:
        return None
    if due >= today:
        return due
    rep = todo.get("repeat")
    if not rep or rep["from"] != "due":
        return None
    try:
        return next_due(todo, today)
    except (OverflowError, ValueError):
        return None


def repeat_text(rep: dict) -> str:
    """ "Repeats every 3 months, counted from when it's done" and the like."""
    every = f"every {rep['unit']}" if rep["every"] == 1 else f"every {rep['every']} {rep['unit']}s"
    return f"Repeats {every}, " + ("counted from when it's done" if rep["from"] == "done" else "on a schedule")


def event_text(todo: dict, names: dict[str, str] | None = None, place: str = "") -> tuple[str, str]:
    """A task's title and details, as its calendar event shows them. names: each user's name, by id. place: the
    area or device it's linked to, by name."""
    lines = []
    if todo.get("category"):
        lines.append(f"Category: {todo['category']}")
    lines.append(f"Priority: {PRI_NAMES.get(todo.get('pri'), 'Medium')}")
    if todo.get("for"):
        lines.append(f"For: {(names or {}).get(todo['for'], 'someone')}")
    if place:
        lines.append(f"Linked to: {place}")
    if todo.get("repeat"):
        lines.append(repeat_text(todo["repeat"]))
    if todo.get("status") == "waiting":
        lines.append("Waiting" + (f" on {todo['waitingOn']}" if todo.get("waitingOn") else ""))
    subs = [sb for sb in todo.get("subs") or [] if sb.get("text", "").strip()]
    if subs:
        lines.append("")
        lines += [("\u2611 " if sb.get("done") else "\u2610 ") + sb["text"].strip() for sb in subs]
    if (todo.get("notes") or "").strip():
        lines += ["", todo["notes"].strip()]
    return todo.get("text") or "(untitled)", "\n".join(lines)


# ---------- what pages are sent ----------

def shown(lst: dict) -> dict:
    """A list as a page is sent it: all but the archive, which is sent only when asked for, and counted instead."""
    out = {k: v for k, v in lst.items() if k != "archive"}
    out["archived"] = len(lst["archive"])
    return out


def snapshot(lst: dict) -> dict:
    """A list as it is now, for list_patch() to compare with once it's changed. Changed tasks and entries are new
    objects, so the ones here are kept as they are."""
    return {"todos": list(lst["todos"]), "done": list(lst["done"]), "notes": lst["notes"],
            "categories": list(lst["categories"]), "archived": len(lst["archive"])}


def list_patch(before: dict, lst: dict) -> dict:
    """What changed in a list since snapshot(), for pages showing it: tasks and entries added or changed ("set"),
    ones removed ("remove"), and the log's order where it isn't just the old order with new entries at the end. The
    open tasks' order, the log's length and its last entry numbers come every time, so a page can check its copy."""
    patch: dict[str, Any] = {"seq": lst["seq"], "todoOrder": [x["id"] for x in lst["todos"]],
                             "doneCount": len(lst["done"]), "doneTail": [x["id"] for x in lst["done"][-TAIL:]]}
    for key in ("todos", "done"):
        was = {id(x) for x in before[key]}
        old_ids = [x["id"] for x in before[key]]
        new_ids = [x["id"] for x in lst[key]]
        part: dict[str, Any] = {}
        changed = [x for x in lst[key] if id(x) not in was]
        if changed:
            part["set"] = changed
        if removed := sorted(set(old_ids) - set(new_ids)):
            part["remove"] = removed
        if key == "done":
            kept, known = set(new_ids), set(old_ids)
            if new_ids != [i for i in old_ids if i in kept] + [x["id"] for x in changed if x["id"] not in known]:
                part["order"] = new_ids
        if part:
            patch[key] = part
    if lst["notes"] != before["notes"]:
        patch["notes"] = lst["notes"]
    if lst["categories"] != before["categories"]:
        patch["categories"] = lst["categories"]
    if len(lst["archive"]) != before["archived"]:
        patch["archived"] = len(lst["archive"])
    return patch


def archive_old(lst: dict, now: int) -> bool:
    """Moves log entries more than a year old into the archive. True if any moved."""
    cutoff = now - ARCHIVE_AFTER_MS
    old = [e for e in lst["done"] if e["ts"] < cutoff]
    if not old:
        return False
    lst["done"] = [e for e in lst["done"] if e["ts"] >= cutoff]
    lst["archive"].extend(old)
    return True


# ---------- notes two people change at once ----------

def _matching_lines(a: list[str], b: list[str]) -> dict[int, int]:
    blocks = difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks()
    return {blk.a + k: blk.b + k for blk in blocks for k in range(blk.size)}


def merge_text(base: str, mine: str, theirs: str) -> str:
    """Notes a page changed from base, merged line by line with what's there now, which someone else may have
    changed meanwhile. Where both changed the same lines, both versions are kept, theirs first, so nothing is lost."""
    if mine == theirs or theirs == base:
        return mine
    if mine == base:
        return theirs
    b, m, t = base.split("\n"), mine.split("\n"), theirs.split("\n")
    in_m, in_t = _matching_lines(b, m), _matching_lines(b, t)
    out: list[str] = []
    bi = mi = ti = 0
    for line in [i for i in range(len(b)) if i in in_m and i in in_t] + [None]:
        bj, mj, tj = (len(b), len(m), len(t)) if line is None else (line, in_m[line], in_t[line])
        cb, cm, ct = b[bi:bj], m[mi:mj], t[ti:tj]
        if cm == cb:
            out += ct
        elif ct in (cb, cm):
            out += cm
        else:
            out += ct + cm
        if line is not None:
            out.append(b[line])
        bi, mi, ti = bj + 1, mj + 1, tj + 1
    return "\n".join(out)


# ---------- requests ----------

def request_events(before: dict, lst: dict, user_id: str) -> tuple[list[dict], list[dict]]:
    """What a change by user_id did with requests, from a snapshot() before it: tasks now for someone else that
    weren't before ("asked"), and requests someone else made that were just ticked off ("finished"). A task brought
    back from the log by Undo isn't asked again."""
    was_for = {x["id"]: x["for"] for x in before["todos"]}
    was_done = {x["id"]: x["for"] for x in before["done"]}
    asked = [t for t in lst["todos"] if t["for"] and t["for"] != user_id and was_for.get(t["id"]) != t["for"]
             and was_done.get(t["id"]) != t["for"]]
    finished = [e for e in lst["done"] if e["id"] not in was_done and e["forBy"] and e["forBy"] != user_id]
    return asked, finished


def due_text(todo: dict) -> str:
    """ " (due Fri Nov 13)", or nothing for a task with no due date."""
    due = parse_date(todo.get("due"))
    return f" (due {due:%a %b} {due.day})" if due else ""
