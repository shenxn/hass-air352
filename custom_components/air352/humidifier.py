"""Native Home Assistant humidifier controls for 352 devices."""
from homeassistant.components.humidifier import (
    HumidifierDeviceClass,
    HumidifierEntity,
    HumidifierEntityFeature,
)
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, DEVICE_TYPE_HUMIDIFIER
from .control import Air352Control
from .select import MODES


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for device in coordinator.devices:
        properties = (coordinator.data or {}).get(device["iotId"], {})
        if (
            (device.get("categoryKey") or "").casefold() == DEVICE_TYPE_HUMIDIFIER
            and {"PowerSwitch", "targetHumidity", "WorkMode"} <= properties.keys()
        ):
            entities.append(Air352Humidifier(coordinator, device))
    async_add_entities(entities)


class Air352Humidifier(Air352Control, HumidifierEntity):
    """Power, humidity and modes backed by confirmed cloud properties."""

    _attr_name = "Humidifier"
    _attr_device_class = HumidifierDeviceClass.HUMIDIFIER
    _attr_supported_features = HumidifierEntityFeature.MODES
    _attr_available_modes = list(MODES)
    _attr_min_humidity = 0
    _attr_max_humidity = 100
    _attr_target_humidity_step = 1

    def __init__(self, coordinator, device):
        super().__init__(coordinator, device, "PowerSwitch")
        self._attr_unique_id = f"{self.iot_id}_humidifier"
        self._attr_translation_key = "humidifier"

    @property
    def is_on(self):
        value = self.read_property("PowerSwitch")
        return None if value is None else bool(value)

    @property
    def current_humidity(self):
        return self.read_property("RelativeHumidity")

    @property
    def target_humidity(self):
        return self.read_property("targetHumidity")

    @property
    def mode(self):
        return next(
            (name for name, value in MODES.items() if value == self.read_property("WorkMode")),
            None,
        )

    async def async_turn_on(self, **kwargs):
        await self.write_value(1, "PowerSwitch")

    async def async_turn_off(self, **kwargs):
        await self.write_value(0, "PowerSwitch")

    async def async_set_humidity(self, humidity):
        if not float(humidity).is_integer() or not self.min_humidity <= humidity <= self.max_humidity:
            raise HomeAssistantError("352 humidity must be an integer between 0 and 100")
        await self.write_value(int(humidity), "targetHumidity")

    async def async_set_mode(self, mode):
        if mode not in MODES:
            raise HomeAssistantError("Unsupported 352 operating mode")
        await self.write_value(MODES[mode], "WorkMode")
