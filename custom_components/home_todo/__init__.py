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

from .const import DOMAIN, PANEL, STATIC_URL

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
FRONTEND_DIR = Path(__file__).parent / "frontend"


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """The page's files, served for as long as Home Assistant runs."""
    await hass.http.async_register_static_paths([StaticPathConfig(STATIC_URL, str(FRONTEND_DIR), cache_headers=False)])
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    version = str((await async_get_integration(hass, DOMAIN)).version)
    # The page runs in a frame of its own, so its styles and keyboard shortcuts stay apart from Home Assistant's.
    # The version in its address makes browsers fetch it afresh after an update.
    await panel_custom.async_register_panel(
        hass, frontend_url_path=PANEL, webcomponent_name="home-todo-panel", sidebar_title="Home To-Do",
        sidebar_icon="mdi:checkbox-marked-outline", module_url=f"{STATIC_URL}/home-todo-panel.js?v={version}",
        embed_iframe=True,
    )
    entry.async_on_unload(lambda: frontend.async_remove_panel(hass, PANEL))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return True
