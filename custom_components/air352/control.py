"""Shared cloud readback for humidifier controls."""
import asyncio

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER


class Air352Control(CoordinatorEntity):
    """Read control state from the coordinator and verify cloud writes."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, device, key):
        super().__init__(coordinator)
        self.iot_id = device["iotId"]
        self.key = key
        self._attr_unique_id = f"{self.iot_id}_{key}"
        self._attr_translation_key = key.lower()
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self.iot_id)},
            "manufacturer": MANUFACTURER,
            "name": device.get("productName", "352 Device"),
        }

    def value(self, key=None):
        prop = (self.coordinator.data or {}).get(self.iot_id, {}).get(key or self.key)
        return prop.get("value") if isinstance(prop, dict) else prop

    @property
    def available(self):
        return super().available and self.value() is not None

    async def write_value(self, value):
        lock = self.coordinator.control_locks.setdefault(self.iot_id, asyncio.Lock())
        async with lock:
            await self._write_and_readback(value)

    async def _write_and_readback(self, value):
        await self.coordinator.api.set_device_properties(self.iot_id, {self.key: value})
        for _ in range(5):
            await asyncio.sleep(3)
            # Read all properties: mode and speed commands can also change power
            # and target humidity. Never fabricate an optimistic local state.
            properties = await self.coordinator.api.get_device_properties(self.iot_id)
            self.coordinator.async_set_updated_data({
                **(self.coordinator.data or {}),
                self.iot_id: properties,
            })
            if self.value() == value:
                return
        raise HomeAssistantError("352 did not confirm the requested setting")
