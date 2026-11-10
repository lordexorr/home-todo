"""Home To-Do's calendars in Home Assistant: one for the Family list, and one for each person who turns theirs on
under Settings on Home To-Do's page. Every calendar is visible to everyone who signs in to Home Assistant, which is
why a personal one is only there when its owner asks for it.

Each shows its list's open tasks that have a due date, as all-day events. A task that repeats on a schedule also shows
on each date it'll be due on after today. A person's calendar also has the Family tasks that are for them."""
from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import area_registry as ar, device_registry as dr, entity_registry as er
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from . import model
from .const import DOMAIN
from .runtime import HomeTodo

PARALLEL_UPDATES = 0


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry[HomeTodo],
                            async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    todo = entry.runtime_data
    calendars: dict[str, HomeTodoCalendar] = {}
    lock = asyncio.Lock()

    async def async_sync() -> None:
        """Adds a calendar for each person who's turned theirs on, and removes any whose owner turned it off."""
        async with lock:
            wanted = {model.FAMILY: "Family"}
            for user_id in todo.calendar_users():
                user = await hass.auth.async_get_user(user_id)
                if user and user.is_active:
                    wanted[user_id] = user.name or "Me"
            registry = er.async_get(hass)
            for reg in er.async_entries_for_config_entry(registry, entry.entry_id):
                if reg.unique_id not in wanted:
                    registry.async_remove(reg.entity_id)
            for list_id in [lid for lid in calendars if lid not in wanted]:
                del calendars[list_id]
            new = [HomeTodoCalendar(todo, entry.entry_id, lid, name)
                   for lid, name in wanted.items() if lid not in calendars]
            for cal in new:
                calendars[cal.list_id] = cal
            if new:
                async_add_entities(new)

    @callback
    def changed(lists: set[str], calendars_changed: bool) -> None:
        # Family's requests are on the calendars of the people they're for too.
        for list_id in set(calendars) if model.FAMILY in lists else lists:
            if (cal := calendars.get(list_id)) is not None:
                cal.refresh()
        if calendars_changed:
            entry.async_create_background_task(hass, async_sync(), "home_todo calendars")

    await async_sync()
    entry.async_on_unload(todo.watch(changed))


class HomeTodoCalendar(CalendarEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, todo: HomeTodo, entry_id: str, list_id: str, name: str) -> None:
        self._todo = todo
        self._added = False
        self.list_id = list_id
        self._attr_name = name
        self._attr_unique_id = list_id
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry_id)}, name=todo.name,
                                            entry_type=DeviceEntryType.SERVICE)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._added = True

    async def async_will_remove_from_hass(self) -> None:
        self._added = False
        await super().async_will_remove_from_hass()

    @callback
    def refresh(self) -> None:
        if self._added:
            self.async_write_ha_state()

    def _tasks(self) -> list[tuple[str, dict[str, Any]]]:
        """(list id, task) for each task on this calendar."""
        lists = self._todo.doc["lists"]
        own = [(self.list_id, t) for t in lists[self.list_id]["todos"]] if self.list_id in lists else []
        if self.list_id == model.FAMILY or not self._todo.can_use(self.list_id, model.FAMILY):
            return own
        return own + [(model.FAMILY, t) for t in lists[model.FAMILY]["todos"] if t["for"] == self.list_id]

    def _event(self, list_id: str, task: dict[str, Any], day: date) -> CalendarEvent:
        summary, description = model.event_text(task, self._todo.names, self._place(task))
        return CalendarEvent(start=day, end=day + timedelta(days=1), summary=summary, description=description or None,
                             uid=f"{list_id}-{task['id']}-{day.isoformat()}")

    def _place(self, task: dict[str, Any]) -> str:
        """The area or device a task is linked to, by name: "Furnace (Basement)", or "Kitchen"."""
        areas = ar.async_get(self.hass)
        if task.get("device") and (device := dr.async_get(self.hass).async_get(task["device"])):
            name = device.name_by_user or device.name or "a device"
            area = areas.async_get_area(device.area_id) if device.area_id else None
            return f"{name} ({area.name})" if area else name
        if task.get("area") and (area := areas.async_get_area(task["area"])):
            return area.name
        return ""

    @property
    def event(self) -> CalendarEvent | None:
        """Today's task, or the next one due."""
        today = dt_util.now().date()
        soonest: tuple[date, str, dict[str, Any]] | None = None
        for list_id, task in self._tasks():
            day = model.next_day(task, today)
            if day is not None and (soonest is None or day < soonest[0]):
                soonest = (day, list_id, task)
        return self._event(soonest[1], soonest[2], soonest[0]) if soonest else None

    async def async_get_events(self, hass: HomeAssistant, start_date: datetime,
                               end_date: datetime) -> list[CalendarEvent]:
        first, last = dt_util.as_local(start_date).date(), dt_util.as_local(end_date).date()
        today = dt_util.now().date()
        events = []
        for list_id, task in self._tasks():
            for day in model.task_days(task, first, last, today):
                event = self._event(list_id, task, day)
                if event.start_datetime_local < end_date and event.end_datetime_local > start_date:
                    events.append(event)
        events.sort(key=lambda e: e.start)
        return events
