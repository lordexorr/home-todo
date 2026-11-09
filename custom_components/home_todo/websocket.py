"""The page's commands. Every user can open Home To-Do, and uses the Family list and their own."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN
from .runtime import HomeTodo


@callback
def async_register(hass: HomeAssistant) -> None:
    for command in (ws_subscribe, ws_apply, ws_prefs):
        websocket_api.async_register_command(hass, command)


def _todo(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> HomeTodo | None:
    if entries := hass.config_entries.async_loaded_entries(DOMAIN):
        return entries[0].runtime_data
    connection.send_error(msg["id"], "not_loaded", "Home To-Do isn't set up.")
    return None


@websocket_api.websocket_command({vol.Required("type"): "home_todo/subscribe"})
@callback
def ws_subscribe(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Everything the user's page shows, then each change to it as it's made, from any page."""
    if not (todo := _todo(hass, connection, msg)):
        return

    @callback
    def forward(payload: dict[str, Any]) -> None:
        connection.send_message(websocket_api.event_message(msg["id"], payload))

    connection.subscriptions[msg["id"]] = todo.subscribe(connection.user.id, forward)
    connection.send_result(msg["id"])
    forward(todo.everything(connection.user))


@websocket_api.websocket_command({
    vol.Required("type"): "home_todo/apply",
    vol.Required("list_id"): str,
    vol.Required("changes"): dict,
})
@callback
def ws_apply(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """What the page changed in one list. Every page showing the list is sent the result before this answers."""
    if not (todo := _todo(hass, connection, msg)):
        return
    if not todo.can_use(connection.user.id, msg["list_id"]):
        connection.send_error(msg["id"], "unauthorized", "That list belongs to someone else.")
        return
    connection.send_result(msg["id"], todo.apply(msg["list_id"], msg["changes"]))


@websocket_api.websocket_command({vol.Required("type"): "home_todo/prefs", vol.Required("prefs"): dict})
@callback
def ws_prefs(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """The user's display settings and links."""
    if not (todo := _todo(hass, connection, msg)):
        return
    connection.send_result(msg["id"], todo.set_prefs(connection.user.id, msg["prefs"]))
