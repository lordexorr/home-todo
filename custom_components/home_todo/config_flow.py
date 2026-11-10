"""Setting up Home To-Do: a single entry, with nothing to fill in. Configure sets the name everyone sees, and who
can only view the Family list or can't see it at all."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.selector import SelectOptionDict, SelectSelector, SelectSelectorConfig, SelectSelectorMode

from .const import CONF_FAMILY_NONE, CONF_FAMILY_VIEW, CONF_NAME, DEFAULT_NAME, DOMAIN, NAME_MAX


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
    """The name shown at the top of the page and in the sidebar, for everyone, and who can only view the Family list
    or can't see it at all. Everyone else can change it."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors = {}
        if user_input is not None:
            view = list(dict.fromkeys(user_input.get(CONF_FAMILY_VIEW) or []))
            none = list(dict.fromkeys(user_input.get(CONF_FAMILY_NONE) or []))
            if set(view) & set(none):
                errors["base"] = "both_lists"
            else:
                name = str(user_input.get(CONF_NAME, "")).strip()[:NAME_MAX] or DEFAULT_NAME
                return self.async_create_entry(data={CONF_NAME: name, CONF_FAMILY_VIEW: view,
                                                     CONF_FAMILY_NONE: none})
        users = await self.hass.auth.async_get_users()
        people = [SelectOptionDict(value=u.id, label=u.name or "Someone")
                  for u in sorted(users, key=lambda u: (u.name or "").lower())
                  if u.is_active and not u.system_generated]
        pick = SelectSelector(SelectSelectorConfig(options=people, multiple=True, mode=SelectSelectorMode.DROPDOWN))
        schema = vol.Schema({vol.Required(CONF_NAME): str, vol.Optional(CONF_FAMILY_VIEW): pick,
                             vol.Optional(CONF_FAMILY_NONE): pick})
        options = self.config_entry.options
        current = user_input or {CONF_NAME: options.get(CONF_NAME) or DEFAULT_NAME,
                                 CONF_FAMILY_VIEW: options.get(CONF_FAMILY_VIEW, []),
                                 CONF_FAMILY_NONE: options.get(CONF_FAMILY_NONE, [])}
        return self.async_show_form(step_id="init", errors=errors,
                                    data_schema=self.add_suggested_values_to_schema(schema, current))
