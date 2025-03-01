"""Base entity for the Fully Kiosk Browser integration."""
from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FullyKioskDataUpdateCoordinator


class FullyKioskEntity(CoordinatorEntity[FullyKioskDataUpdateCoordinator], Entity):
    """Defines a Fully Kiosk Browser entity."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: FullyKioskDataUpdateCoordinator) -> None:
        """Initialize the Fully Kiosk Browser entity."""
        super().__init__(coordinator=coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.data["deviceID"])},
            name=coordinator.data["deviceName"],
            manufacturer=coordinator.data["deviceManufacturer"],
            model=coordinator.data["deviceModel"],
            sw_version=coordinator.data["appVersionName"],
            configuration_url=f"http://{coordinator.data['ip4']}:2323",
        )
