"""Home To-Do's lists while Home Assistant runs: kept in .storage/home_todo, changed by the page's commands, and
pushed to every open page that shows them and to the calendars."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from homeassistant.auth.models import User
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import Store

from . import model
from .const import SAVE_DELAY, STORAGE_KEY, STORAGE_VERSION

type Listener = Callable[[dict[str, Any]], None]
type Watcher = Callable[[set[str], bool], None]  # the lists that changed, and whether calendar settings did


class HomeTodo:
    def __init__(self, hass: HomeAssistant, name: str, version: str) -> None:
        self.hass = hass
        self.name = name
        self.version = version  # a page from another version stops and asks to be reloaded
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.doc: dict[str, Any] = model.new_doc()
        self._listeners: dict[object, tuple[str, Listener]] = {}
        self._watchers: list[Watcher] = []

    async def async_load(self) -> None:
        self.doc = model.norm_doc(await self._store.async_load())

    async def async_stop(self) -> None:
        """Saves straight away, and tells every open page to connect again."""
        for _user_id, listener in list(self._listeners.values()):
            listener({"closed": True})
        self._listeners.clear()
        await self._store.async_save(self.doc)

    @staticmethod
    def can_use(user_id: str, list_id: str) -> bool:
        """Everyone uses the Family list, and only its owner uses a personal list, administrators included."""
        return list_id in (model.FAMILY, user_id)

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

    @callback
    def everything(self, user: User) -> dict[str, Any]:
        """All a user's page shows, for when it opens or reconnects."""
        if model.ensure_personal(self.doc, user.id):
            self._changed()
        return {
            "initial": True,
            "rev": self.doc["rev"],
            "name": self.name,
            "version": self.version,
            "user": {"id": user.id, "name": user.name or "", "is_admin": user.is_admin},
            "lists": {lid: self.doc["lists"][lid] for lid in (model.FAMILY, user.id)},
            "prefs": self.doc["prefs"].get(user.id, {}),
        }

    @callback
    def apply(self, list_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        if list_id != model.FAMILY:
            model.ensure_personal(self.doc, list_id)
        remap = model.apply_changes(self.doc, list_id, changes)
        self._changed()
        self._publish({list_id})
        self._tell({list_id}, calendars=False)
        return {"rev": self.doc["rev"], "remap": remap}

    @callback
    def set_prefs(self, user_id: str, prefs: dict[str, Any]) -> dict[str, Any]:
        before = self.calendar_users()
        self.doc["prefs"][user_id] = model.norm_prefs(prefs)
        self._changed()
        self._publish(set(), prefs_for=user_id)
        self._tell(set(), calendars=self.calendar_users() != before)
        return {"rev": self.doc["rev"]}

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
    def _publish(self, lists: set[str], prefs_for: str | None = None) -> None:
        """Sends each open page what changed that it shows."""
        for user_id, listener in list(self._listeners.values()):
            payload: dict[str, Any] = {"rev": self.doc["rev"]}
            shown = {lid: self.doc["lists"][lid] for lid in lists if self.can_use(user_id, lid)}
            if shown:
                payload["lists"] = shown
            if prefs_for == user_id:
                payload["prefs"] = self.doc["prefs"].get(user_id, {})
            if len(payload) > 1:
                listener(payload)
