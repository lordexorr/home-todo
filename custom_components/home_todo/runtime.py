"""Home To-Do's lists while Home Assistant runs: kept in .storage/home_todo, changed by the page's commands, and
pushed to every open page that shows them and to the calendars."""
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import voluptuous as vol

from homeassistant.auth.models import User
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.storage import Store

from . import model
from .const import PANEL, SAVE_DELAY, STORAGE_KEY, STORAGE_VERSION

_LOGGER = logging.getLogger(__package__)

type Listener = Callable[[dict[str, Any]], None]
type Watcher = Callable[[set[str], bool], None]  # the lists that changed, and whether calendar settings did


class HomeTodo:
    def __init__(self, hass: HomeAssistant, name: str, version: str, view_only: Any = (),
                 no_access: Any = ()) -> None:
        self.hass = hass
        self.name = name
        self.version = version  # a page from another version stops and asks to be reloaded
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.doc: dict[str, Any] = model.new_doc()
        self._listeners: dict[object, tuple[str, Listener]] = {}
        self._watchers: list[Watcher] = []
        self.names: dict[str, str] = {}  # everyone with a login, by user id
        self.view_only, self.no_access = set(view_only), set(no_access)  # set under Configure

    async def async_load(self) -> None:
        self.doc = model.norm_doc(await self._store.async_load())
        await self.async_people()
        self.archive_old()

    async def async_stop(self) -> None:
        """Saves straight away, and tells every open page to connect again."""
        for _user_id, listener in list(self._listeners.values()):
            listener({"closed": True})
        self._listeners.clear()
        await self._store.async_save(self.doc)

    def family_access(self, user_id: str) -> str:
        """ "edit", "view" or "none", as set under Configure. Everyone can change Family unless they're listed there."""
        return "none" if user_id in self.no_access else "view" if user_id in self.view_only else "edit"

    def can_use(self, user_id: str, list_id: str) -> bool:
        """Only its owner sees a personal list, administrators included, and Family is seen by everyone with access."""
        return list_id == user_id or (list_id == model.FAMILY and self.family_access(user_id) != "none")

    def can_edit(self, user_id: str, list_id: str) -> bool:
        return list_id == user_id or (list_id == model.FAMILY and self.family_access(user_id) == "edit")

    @callback
    def subscribe(self, user_id: str, listener: Listener) -> Callable[[], None]:
        key = object()
        self._listeners[key] = (user_id, listener)

        @callback
        def remove() -> None:
            self._listeners.pop(key, None)

        return remove

    @callback
    def watch(self, watcher: Watcher) -> Callable[[], None]:
        """For the calendars: called after every change."""
        self._watchers.append(watcher)

        @callback
        def remove() -> None:
            if watcher in self._watchers:
                self._watchers.remove(watcher)

        return remove

    @callback
    def calendar_users(self) -> list[str]:
        """Everyone who's chosen to have their own list on Home Assistant's calendar."""
        return [uid for uid, prefs in self.doc["prefs"].items()
                if prefs.get("cfg", {}).get("calendar") and uid in self.doc["lists"]]

    async def async_people(self) -> list[dict[str, str]]:
        """Everyone with a Home Assistant login, who a request can be for."""
        users = await self.hass.auth.async_get_users()
        people = sorted(({"id": u.id, "name": u.name or "Someone"} for u in users
                         if u.is_active and not u.system_generated), key=lambda p: p["name"].lower())
        self.names = {p["id"]: p["name"] for p in people}
        return people

    @callback
    def everything(self, user: User, people: list[dict[str, str]]) -> dict[str, Any]:
        """All a user's page shows, for when it opens or reconnects."""
        if model.ensure_personal(self.doc, user.id):
            self._changed()
        return {
            "initial": True,
            "rev": self.doc["rev"],
            "name": self.name,
            "version": self.version,
            "user": {"id": user.id, "name": user.name or "", "is_admin": user.is_admin},
            "people": [{**p, "family": self.family_access(p["id"])} for p in people],
            "lists": {lid: model.shown(self.doc["lists"][lid]) for lid in (model.FAMILY, user.id)
                      if self.can_use(user.id, lid)},
            "access": {"family": self.family_access(user.id)},
            "prefs": self.doc["prefs"].get(user.id, {}),
        }

    @callback
    def apply(self, list_id: str, changes: dict[str, Any], user: User) -> dict[str, Any]:
        """What a page changed in a list, as user. Anyone a task is newly for is told, and so is whoever asked
        for one that's been ticked off."""
        if list_id != model.FAMILY:
            model.ensure_personal(self.doc, list_id)
        if list_id == model.FAMILY:
            self._only_for_editors(changes)
        lst = self.doc["lists"][list_id]
        before = model.snapshot(lst)
        remap = model.apply_changes(self.doc, list_id, changes, user_id=user.id)
        self._changed()
        self._publish({list_id: model.list_patch(before, lst)})
        self._tell({list_id}, calendars=False)
        asked, finished = model.request_events(before, lst, user.id)
        who = user.name or "Someone"
        for task in asked:
            self._notify(task["for"], f"{who} asked you: {task['text'] or '(untitled)'}{model.due_text(task)}")
        for entry in finished:
            self._notify(entry["forBy"], f"{who} finished: {entry['text'] or '(untitled)'}")
        return {"rev": self.doc["rev"], "remap": remap}

    def _only_for_editors(self, changes: Any) -> None:
        """A request can only be for someone who can change Family, so they can tick it off."""
        todos = changes.get("todos") if isinstance(changes, dict) else None
        if not isinstance(todos, dict):
            return
        for key in ("add", "update"):
            for raw in todos.get(key) if isinstance(todos.get(key), list) else []:
                if isinstance(raw, dict) and isinstance(raw.get("for"), str) and raw["for"] \
                        and self.family_access(raw["for"]) != "edit":
                    raw["for"] = ""

    @callback
    def _notify(self, user_id: str, message: str) -> None:
        """Tells a person, through where they chose under Settings. Nobody is told if they haven't chosen."""
        target = self.doc["prefs"].get(user_id, {}).get("cfg", {}).get("notify", "")
        if target:
            self.hass.async_create_background_task(self._async_notify(target, message), "home_todo_notify")

    async def _async_notify(self, target: str, message: str) -> None:
        service = target.partition(".")[2]
        data: dict[str, Any] = {"title": self.name, "message": message}
        if service.startswith("mobile_app_"):  # tapping it opens Home To-Do, on iPhone and Android
            data["data"] = {"url": f"/{PANEL}", "clickAction": f"/{PANEL}"}
        try:
            await self.hass.services.async_call("notify", service, data, blocking=True)
        except (HomeAssistantError, vol.Invalid) as err:
            _LOGGER.warning("Couldn't send a Home To-Do notification through %s: %s", target, err)

    @callback
    def set_prefs(self, user_id: str, prefs: dict[str, Any]) -> dict[str, Any]:
        before = self.calendar_users()
        self.doc["prefs"][user_id] = model.norm_prefs(prefs)
        self._changed()
        self._publish({}, prefs_for=user_id)
        self._tell(set(), calendars=self.calendar_users() != before)
        return {"rev": self.doc["rev"]}

    @callback
    def archive(self, list_id: str) -> list[dict[str, Any]]:
        """A list's log entries more than a year old, for a page that asks to see them."""
        return self.doc["lists"][list_id]["archive"] if list_id in self.doc["lists"] else []

    @callback
    def archive_old(self, _now: Any = None) -> None:
        """Moves log entries more than a year old into each list's archive. Run at startup and once a day."""
        patches = {}
        for list_id, lst in self.doc["lists"].items():
            before = model.snapshot(lst)
            if model.archive_old(lst, model.now_ms()):
                patches[list_id] = model.list_patch(before, lst)
        if patches:
            self._changed()
            self._publish(patches)

    @callback
    def _changed(self) -> None:
        self.doc["rev"] += 1
        self._store.async_delay_save(lambda: self.doc, SAVE_DELAY)

    @callback
    def _tell(self, lists: set[str], calendars: bool) -> None:
        if lists or calendars:
            for watcher in list(self._watchers):
                watcher(lists, calendars)

    @callback
    def _publish(self, patches: dict[str, dict[str, Any]], prefs_for: str | None = None) -> None:
        """Sends each open page what changed in the lists it shows, and its owner's settings if they changed."""
        for user_id, listener in list(self._listeners.values()):
            payload: dict[str, Any] = {"rev": self.doc["rev"]}
            if mine := {lid: patch for lid, patch in patches.items() if self.can_use(user_id, lid)}:
                payload["patches"] = mine
            if prefs_for == user_id:
                payload["prefs"] = self.doc["prefs"].get(user_id, {})
            if len(payload) > 1:
                listener(payload)
