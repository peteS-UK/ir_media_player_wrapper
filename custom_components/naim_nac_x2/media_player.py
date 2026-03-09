from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant import config_entries, core
from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.const import CONF_NAME
from homeassistant.helpers import (
    config_validation as cv,
    entity_platform,
)
from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    DOMAIN,
    SERVICE_SEND_COMMAND,
    CONF_REMOTE_ENTITY,
    BROADLINK_COMMANDS,
    MANUFACTURER,
    MODEL,
    CONF_INPUT1,
    CONF_INPUT2,
    CONF_INPUT3,
    CONF_INPUT4,
    CONF_INPUT5,
    CONF_INPUT6,
    CONF_REMOTE_TYPE,
    TUYA_COMMANDS,
)

_LOGGER = logging.getLogger(__name__)

SUPPORT = (
    MediaPlayerEntityFeature.VOLUME_STEP
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.SELECT_SOURCE
)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
) -> None:
    _source_map = {
        "one": config_entry.data[CONF_INPUT1],
        "two": config_entry.data[CONF_INPUT2],
        "three": config_entry.data[CONF_INPUT3],
        "four": config_entry.data[CONF_INPUT4],
        "five": config_entry.data[CONF_INPUT5],
        "six": config_entry.data[CONF_INPUT6],
    }
    async_add_entities(
        [
            Device(
                hass,
                config_entry.data[CONF_NAME],
                config_entry.data[CONF_REMOTE_ENTITY],
                config_entry.data[CONF_REMOTE_TYPE],
                _source_map,
            )
        ]
    )

    # Register entity services
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_SEND_COMMAND,
        {
            vol.Required("command"): cv.string,
        },
        Device.send_command.__name__,
    )


class Device(MediaPlayerEntity):
    # Representation of a NAC

    def __init__(self, hass, name, remote_entity, remote_type, source_map):
        self._hass = hass
        self._state = MediaPlayerState.IDLE
        self._entity_id = f"media_player.{DOMAIN}"
        self._unique_id = f"{DOMAIN}_" + name.replace(" ", "_").replace(
            "-", "_"
        ).replace(":", "_")
        self._device_class = "receiver"
        self._name = name
        self._remote_entity = remote_entity
        self._remote_type = remote_type
        self._source_map = source_map
        self._source = None
        self._sources = list(self._source_map.values())

    async def async_select_source(self, source: str) -> None:
        self._source = source
        _cmd = [key for key, val in self._source_map.items() if val == source]
        await self._send_remote_command(_cmd[0])
        self.async_schedule_update_ha_state()

    @property
    def source_list(self):
        return self._sources

    @property
    def source(self):
        return self._source

    @property
    def should_poll(self):
        return False

    @property
    def icon(self):
        return "mdi:audio-video"

    @property
    def state(self) -> MediaPlayerState:
        return MediaPlayerState.ON

    @property
    def name(self):
        return None

    @property
    def has_entity_name(self):
        return True

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self._unique_id)
            },
            name=self._name,
            manufacturer=MANUFACTURER,
            model=MODEL,
        )

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def entity_id(self):
        return self._entity_id

    @property
    def device_class(self):
        return self._device_class

    @entity_id.setter
    def entity_id(self, entity_id):
        self._entity_id = entity_id

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        return SUPPORT

    async def _send_remote_command(self, command):
        if self._remote_type == "Tuya RC5":
            await self.hass.services.async_call(
                "remote",
                "send_command",
                {
                    "entity_id": self._remote_entity,
                    "num_repeats": "1",
                    "delay_secs": "0.4",
                    "command": f"{TUYA_COMMANDS[command]['rc5']}",
                },
            )
        if self._remote_type == "Tuya Raw":
            await self.hass.services.async_call(
                "remote",
                "send_command",
                {
                    "entity_id": self._remote_entity,
                    "num_repeats": "1",
                    "delay_secs": "0.4",
                    "command": f"{TUYA_COMMANDS[command]['raw']}",
                },
            )

        if self._remote_type == "Broadlink":
            await self.hass.services.async_call(
                "remote",
                "send_command",
                {
                    "entity_id": self._remote_entity,
                    "num_repeats": "1",
                    "delay_secs": "0.4",
                    "command": f"b64:{BROADLINK_COMMANDS[command]}",
                },
            )

    @property
    def is_volume_muted(self):
        return False

    async def async_mute_volume(self, mute: bool) -> None:
        await self._send_remote_command("mute")

    async def async_volume_up(self):
        await self._send_remote_command("vol+")

    async def async_volume_down(self):
        await self._send_remote_command("vol-")

    async def send_command(self, command):
        await self._send_remote_command(command)
