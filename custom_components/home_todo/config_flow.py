"""Setting up Home To-Do: a single entry, with nothing to fill in. Configure sets the name everyone sees."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback

from .const import CONF_NAME, DEFAULT_NAME, DOMAIN, NAME_MAX


class HomeTodoConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="Home To-Do", data={}, options={CONF_NAME: DEFAULT_NAME})
        return self.async_show_form(step_id="user")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return HomeTodoOptionsFlow()


class HomeTodoOptionsFlow(OptionsFlow):
    """The name shown at the top of the page and in the sidebar, for everyone."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            name = str(user_input.get(CONF_NAME, "")).strip()[:NAME_MAX] or DEFAULT_NAME
            return self.async_create_entry(data={CONF_NAME: name})
        schema = vol.Schema({vol.Required(CONF_NAME): str})
        return self.async_show_form(step_id="init", data_schema=self.add_suggested_values_to_schema(
            schema, {CONF_NAME: self.config_entry.options.get(CONF_NAME) or DEFAULT_NAME}))
