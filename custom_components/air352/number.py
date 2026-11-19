"""Numeric controls for 352 humidifiers."""
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, DEVICE_TYPE_HUMIDIFIER
from .control import Air352Control


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for device in coordinator.devices:
        if (device.get("categoryKey") or "").casefold() != DEVICE_TYPE_HUMIDIFIER:
            continue
        properties = (coordinator.data or {}).get(device["iotId"], {})
        for key in ("targetHumidity", "WindSpeed"):
            if key in properties:
                entities.append(Air352Number(coordinator, device, key))
    async_add_entities(entities)


class Air352Number(Air352Control, NumberEntity):
    """A target humidity or fan speed setting."""

    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator, device, key):
        super().__init__(coordinator, device, key)
        self._attr_native_min_value = 0
        self._attr_native_step = 1
        if key == "targetHumidity":
            self._attr_name = "Target Humidity"
            self._attr_native_max_value = 100
            self._attr_native_unit_of_measurement = "%"
            self._attr_icon = "mdi:water-percent"
        else:
            self._attr_name = "Fan Speed"
            self._attr_native_max_value = 6
            self._attr_icon = "mdi:fan"

    @property
    def native_value(self):
        return self.read_property()

    async def async_set_native_value(self, value):
        if not float(value).is_integer() or not self.native_min_value <= value <= self.native_max_value:
            raise HomeAssistantError("352 setting is outside the supported integer range")
        await self.write_value(int(value))
