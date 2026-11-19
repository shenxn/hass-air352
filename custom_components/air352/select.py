"""Normal operating modes for 352 humidifiers."""
from homeassistant.components.select import SelectEntity
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, DEVICE_TYPE_HUMIDIFIER
from .control import Air352Control

# Working states (drying, sterilizing) are deliberately not offered as commands.
MODES = {"auto": 1, "sleep": 2, "manual": 4}


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        Air352Mode(coordinator, device, "WorkMode")
        for device in coordinator.devices
        if (device.get("categoryKey") or "").casefold() == DEVICE_TYPE_HUMIDIFIER
        and "WorkMode" in (coordinator.data or {}).get(device["iotId"], {})
    )


class Air352Mode(Air352Control, SelectEntity):
    """Mode selection; the device may turn on when its mode changes."""

    _attr_name = "Operating Mode"
    _attr_options = list(MODES)
    _attr_icon = "mdi:air-humidifier"

    @property
    def current_option(self):
        return next((name for name, value in MODES.items() if value == self.value()), None)

    async def async_select_option(self, option):
        if option not in MODES:
            raise HomeAssistantError("Unsupported 352 operating mode")
        await self.write_value(MODES[option])
