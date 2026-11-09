"""Home To-Do: task lists for the house, on a page in Home Assistant's sidebar."""
from __future__ import annotations

from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import async_get_integration

from . import websocket
from .const import CONF_NAME, DEFAULT_NAME, DOMAIN, PANEL, STATIC_URL
from .runtime import HomeTodo

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
FRONTEND_DIR = Path(__file__).parent / "frontend"

type HomeTodoConfigEntry = ConfigEntry[HomeTodo]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """What stays for as long as Home Assistant runs: the page's commands and files."""
    websocket.async_register(hass)
    await hass.http.async_register_static_paths([StaticPathConfig(STATIC_URL, str(FRONTEND_DIR), cache_headers=False)])
    return True


async def async_setup_entry(hass: HomeAssistant, entry: HomeTodoConfigEntry) -> bool:
    name = entry.options.get(CONF_NAME) or DEFAULT_NAME
    todo = HomeTodo(hass, name)
    await todo.async_load()
    entry.runtime_data = todo
    version = str((await async_get_integration(hass, DOMAIN)).version)
    # The page runs in a frame of its own, so its styles and keyboard shortcuts stay apart from Home Assistant's.
    # The version in its address makes browsers fetch it afresh after an update.
    await panel_custom.async_register_panel(
        hass, frontend_url_path=PANEL, webcomponent_name="home-todo-panel", sidebar_title=name,
        sidebar_icon="mdi:checkbox-marked-outline", module_url=f"{STATIC_URL}/home-todo-panel.js?v={version}",
        embed_iframe=True,
    )
    entry.async_on_unload(lambda: frontend.async_remove_panel(hass, PANEL))
    # A new name under Configure starts everything again, so the sidebar and every open page show it.
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: HomeTodoConfigEntry) -> bool:
    await entry.runtime_data.async_stop()
    return True


async def _async_reload(hass: HomeAssistant, entry: HomeTodoConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
