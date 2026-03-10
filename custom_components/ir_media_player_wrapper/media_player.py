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
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import (
    config_validation as cv,
)
from homeassistant.helpers import (
    entity_platform,
)
from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    CONF_FEATURES_LIST,
    CONF_IR_DEVICE,
    CONF_MANUFACTURER,
    CONF_MODEL,
    CONF_REMOTE_ENTITY,
    CONF_SOURCE_LIST,
    DOMAIN,
    SERVICE_SET_STATE,
)

_LOGGER = logging.getLogger(__name__)

STATE_MAP = {
    "Off": MediaPlayerState.OFF,
    "On": MediaPlayerState.ON,
    "Idle": MediaPlayerState.IDLE,
    "Playing": MediaPlayerState.PLAYING,
    "Paused": MediaPlayerState.PAUSED,
    "Buffering": MediaPlayerState.BUFFERING,
}

FEATURE_MAP = {
    "Play": MediaPlayerEntityFeature.PLAY,
    "Pause": MediaPlayerEntityFeature.PAUSE,
    "Stop": MediaPlayerEntityFeature.STOP,
    "Next": MediaPlayerEntityFeature.NEXT_TRACK,
    "Previous": MediaPlayerEntityFeature.PREVIOUS_TRACK,
    "Mute": MediaPlayerEntityFeature.VOLUME_MUTE,
    "Volume Up/Volume Down": MediaPlayerEntityFeature.VOLUME_STEP,
    "Turn On": MediaPlayerEntityFeature.TURN_ON,
    "Turn Off": MediaPlayerEntityFeature.TURN_OFF,
    "Sources": MediaPlayerEntityFeature.SELECT_SOURCE,
}


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
) -> None:
    async_add_entities([Device(config_entry)])

    # Register entity services
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_SET_STATE,
        {
            vol.Required("state"): cv.string,
        },
        Device.set_state.__name__,
    )


class Device(MediaPlayerEntity):
    # Representation of a NAC

    def __init__(self, config_entry):

        self._entity_id = f"media_player.{DOMAIN}"
        self._name = config_entry.data[CONF_NAME]
        self._unique_id = f"{DOMAIN}_" + self._name.replace(" ", "_").replace(
            "-", "_"
        ).replace(":", "_")
        self._device_class = "receiver"
        self._manufacturer = config_entry.data[CONF_MANUFACTURER]
        self._model = config_entry.data[CONF_MODEL]
        self._remote_entity = config_entry.data[CONF_REMOTE_ENTITY]
        self._source_list = config_entry.options.get(
            CONF_SOURCE_LIST, config_entry.data.get(CONF_SOURCE_LIST, [])
        )
        self._selected_features = config_entry.options.get(
            CONF_FEATURES_LIST, config_entry.data.get(CONF_FEATURES_LIST, [])
        )
        self._state = (
            MediaPlayerState.OFF
            if "Turn On" in self._selected_features
            else MediaPlayerState.ON
        )
        self._ir_device = config_entry.data[CONF_IR_DEVICE]
        self._source = None
        self._muted = False

        features = MediaPlayerEntityFeature(0)
        for feature in self._selected_features:
            if feature in FEATURE_MAP:
                features |= FEATURE_MAP[feature]
        self._attr_supported_features = features

    async def async_select_source(self, source: str) -> None:
        self._source = source
        await self._send_remote_command(source)
        self.async_schedule_update_ha_state()

    @property
    def source_list(self):
        return self._source_list

    @property
    def source(self):
        return self._source

    @property
    def should_poll(self):
        return False

    @property
    def icon(self):
        if self._state == MediaPlayerState.OFF:
            return "mdi:audio-video-off"
        else:
            return "mdi:audio-video"

    @property
    def state(self) -> MediaPlayerState:
        return self._state

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
            manufacturer=self._manufacturer,
            model=self._model,
        )

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def device_class(self):
        return self._device_class

    async def _send_remote_command(self, command):

        try:
            await self.hass.services.async_call(
                "remote",
                "send_command",
                {
                    "entity_id": self._remote_entity,
                    "device": self._ir_device,
                    "num_repeats": "1",
                    "delay_secs": "0.4",
                    "command": command,
                },
            )
        except Exception as e:
            raise HomeAssistantError(f"Failed to send command {command}: {e}")

    async def set_state(self, state):
        if state not in STATE_MAP:
            raise HomeAssistantError(f"Invalid state: {state}")
        self._state = STATE_MAP[state]
        self.async_schedule_update_ha_state()

    @property
    def is_volume_muted(self):
        return self._muted

    async def async_mute_volume(self, mute: bool) -> None:
        await self._send_remote_command("Mute")
        self._muted = mute
        self.async_schedule_update_ha_state()

    async def async_volume_up(self):
        await self._send_remote_command("Volume Up")

    async def async_volume_down(self):
        await self._send_remote_command("Volume Down")

    async def send_command(self, command):
        await self._send_remote_command(command)

    async def async_media_stop(self) -> None:
        """Send stop command to media player."""
        await self._send_remote_command("Stop")
        self._state = MediaPlayerState.IDLE
        self.async_schedule_update_ha_state()

    async def async_media_play(self) -> None:
        """Send play command to media player."""
        await self._send_remote_command("Play")
        self._state = MediaPlayerState.PLAYING
        self.async_schedule_update_ha_state()

    async def async_media_pause(self) -> None:
        """Send pause command to media player."""
        await self._send_remote_command("Pause")
        self._state = MediaPlayerState.PAUSED
        self.async_schedule_update_ha_state()

    async def async_media_next_track(self) -> None:
        """Send next track command."""
        await self._send_remote_command("Next")

    async def async_media_previous_track(self) -> None:
        """Send next track command."""
        await self._send_remote_command("Previous")

    async def async_turn_on(self) -> None:
        """Send turn on command."""
        await self._send_remote_command("Turn On")
        self._state = MediaPlayerState.ON
        self.async_schedule_update_ha_state()

    async def async_turn_off(self) -> None:
        """Send turn off command."""
        await self._send_remote_command("Turn Off")
        self._state = MediaPlayerState.OFF
        self.async_schedule_update_ha_state()
