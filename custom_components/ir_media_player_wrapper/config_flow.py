import logging

from typing import Dict

import voluptuous as vol

from .const import (
    DOMAIN,
    CONF_REMOTE_ENTITY,
    CONF_IR_DEVICE,
    CONF_SOURCE_LIST,
    CONF_FEATURES_LIST,
    CONF_MANUFACTURER, 
    CONF_MODEL, 
)

from homeassistant.core import callback

from homeassistant.config_entries import (
    ConfigEntry,
)

from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    SelectSelector,
    SelectSelectorConfig,
)

from homeassistant import config_entries, core, exceptions
from homeassistant.const import CONF_NAME
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_MANUFACTURER): cv.string,
        vol.Required(CONF_MODEL): cv.string,
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_REMOTE_ENTITY): EntitySelector(
            EntitySelectorConfig(filter={"domain": "remote"})
        ),
        vol.Required(CONF_IR_DEVICE): cv.string,
        vol.Required(CONF_FEATURES_LIST, default=["Play", "Pause", "Stop", "Next", "Previous", "Mute", "Volume Up/Volume Down", "Turn On", "Turn Off", "Sources"]): SelectSelector(
            SelectSelectorConfig(options=["Play", "Pause", "Stop", "Next", "Previous", "Mute", "Volume Up/Volume Down", "Turn On", "Turn Off", "Sources"], custom_value=False, multiple=True)
        ),
        vol.Optional(CONF_SOURCE_LIST, default=[]): SelectSelector(
            SelectSelectorConfig(options=["Phono", "CD", "DVD", "Game", "BluRay", "TV","Aux", "Spotify", "Radio"], custom_value=True, multiple=True)
        ),
    }
)


class SelectError(exceptions.HomeAssistantError):
    """Error"""

    pass


async def validate_auth(hass: core.HomeAssistant, data: dict) -> None:
    if "name" not in data.keys():
        data["name"] = ""

    if len(data["name"]) < 1:
        # Manual entry requires host and name and model
        raise ValueError


@config_entries.HANDLERS.register(DOMAIN)
class ConfigFlow(config_entries.ConfigFlow):
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlowHandler:
        """Get the options flow for this handler."""
        return OptionsFlowHandler()

    async def async_step_user(self, user_input=None):
        """Invoked when a user initiates a flow via the user interface."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            try:
                await validate_auth(self.hass, user_input)
            except ValueError:
                errors["base"] = "data"

            if not errors:
                # Input is valid, set data.
                self.data = user_input
                return self.async_create_entry(
                    title=self.data[CONF_NAME], data=self.data
                )



        # If there is no user input or there were errors, show the form again, including any errors that were found with the input.
        return self.async_show_form(
            step_id="user", data_schema=CONFIG_SCHEMA, errors=errors
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for your integration."""

    def __init__(self) -> None:
        """Initialize options flow."""


    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            # Save the new options into config_entry.options
            return self.async_create_entry(title="", data=user_input)

        # 1. Get current values to use as defaults.
        # We check .options first. If empty, we fall back to .data (initial setup).
        # If both are empty, we fall back to the base defaults.
        current_features = self.config_entry.options.get(
            CONF_FEATURES_LIST, 
            self.config_entry.data.get(CONF_FEATURES_LIST, ["Play", "Pause", "Stop", "Next", "Previous", "Mute", "Volume Up/Volume Down", "Turn On", "Turn Off", "Sources"])
        )
        
        current_sources = self.config_entry.options.get(
            CONF_SOURCE_LIST, 
            self.config_entry.data.get(CONF_SOURCE_LIST, [])
        )

        # 2. Build the schema dynamically using the retrieved values
        options_schema = vol.Schema(
            {
                vol.Required(CONF_FEATURES_LIST, default=current_features): SelectSelector(
                    SelectSelectorConfig(
                        options=["Play", "Pause", "Stop", "Next", "Previous", "Mute", "Volume Up/Volume Down", "Turn On", "Turn Off", "Sources"], 
                        custom_value=False, 
                        multiple=True
                    )
                ),
                vol.Optional(CONF_SOURCE_LIST, default=current_sources): SelectSelector(
                    SelectSelectorConfig(
                        options=["Phono", "CD", "DVD", "Game", "BluRay", "TV", "Aux", "Spotify", "Radio"], 
                        custom_value=True, 
                        multiple=True
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
        )
