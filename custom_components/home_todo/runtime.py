"""Home To-Do's lists while Home Assistant runs: kept in .storage/home_todo, changed by the page's commands, and
pushed to every open page that shows them."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from homeassistant.auth.models import User
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import Store

from . import model
from .const import SAVE_DELAY, STORAGE_KEY, STORAGE_VERSION

type Listener = Callable[[dict[str, Any]], None]


class HomeTodo:
    def __init__(self, hass: HomeAssistant, name: str) -> None:
        self.hass = hass
        self.name = name
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.doc: dict[str, Any] = model.new_doc()
        self._listeners: dict[object, tuple[str, Listener]] = {}

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
    def everything(self, user: User) -> dict[str, Any]:
        """All a user's page shows, for when it opens or reconnects."""
        if model.ensure_personal(self.doc, user.id):
            self._changed()
        return {
            "initial": True,
            "rev": self.doc["rev"],
            "name": self.name,
            "user": {"id": user.id, "name": user.name or "", "is_admin": user.is_admin},
            "lists": {lid: self.doc["lists"][lid] for lid in (model.FAMILY, user.id)},
            "categories": self.doc["categories"],
            "prefs": self.doc["prefs"].get(user.id, {}),
        }

    @callback
    def apply(self, list_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        if list_id != model.FAMILY:
            model.ensure_personal(self.doc, list_id)
        categories = list(self.doc["categories"])
        remap = model.apply_changes(self.doc, list_id, changes)
        self._changed()
        self._publish({list_id}, categories=self.doc["categories"] != categories)
        return {"rev": self.doc["rev"], "remap": remap}

    @callback
    def set_prefs(self, user_id: str, prefs: dict[str, Any]) -> dict[str, Any]:
        self.doc["prefs"][user_id] = model.norm_prefs(prefs)
        self._changed()
        self._publish(set(), prefs_for=user_id)
        return {"rev": self.doc["rev"]}

    @callback
    def _changed(self) -> None:
        self.doc["rev"] += 1
        self._store.async_delay_save(lambda: self.doc, SAVE_DELAY)

    @callback
    def _publish(self, lists: set[str], categories: bool = False, prefs_for: str | None = None) -> None:
        """Sends each open page what changed that it shows. Categories go to everyone when they change, since every
        list shares them."""
        for user_id, listener in list(self._listeners.values()):
            payload: dict[str, Any] = {"rev": self.doc["rev"]}
            shown = {lid: self.doc["lists"][lid] for lid in lists if self.can_use(user_id, lid)}
            if shown:
                payload["lists"] = shown
            if shown or categories:
                payload["categories"] = self.doc["categories"]
            if prefs_for == user_id:
                payload["prefs"] = self.doc["prefs"].get(user_id, {})
            if len(payload) > 1:
                listener(payload)
