"""
Setup for different kinds of Tuya climate devices
"""
import logging

from . import DOMAIN
from .const import (
    CONF_CLIMATE,
    CONF_DEVICE_ID,
    CONF_TYPE,
)
from .generic.climate import TuyaLocalClimate
from .helpers.device_config import get_config

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Tuya device according to its type."""
    data = hass.data[DOMAIN][discovery_info[CONF_DEVICE_ID]]
    device = data["device"]

    cfg = get_config(discovery_info[CONF_TYPE])
    if cfg is None:
        raise ValueError(f"No device config found for {discovery_info}")
    ecfg = cfg.primary_entity
    if ecfg.entity != "climate":
        for ecfg in cfg.secondary_entities():
            if ecfg.entity == "climate":
                break
        if ecfg.entity != "climate":
            raise ValueError(f"{device.name} does not support use as a climate device.")
    if ecfg.deprecated:
        _LOGGER.warning(ecfg.deprecation_message)

    legacy_class = ecfg.legacy_class
    # Transition: generic climate entity exists, but is not complete. More
    # complex climate devices still need a device specific class.
    # If legacy_class exists, use it, otherwise use the generic climate class.
    if legacy_class is not None:
        data[CONF_CLIMATE] = legacy_class(device)
    else:
        data[CONF_CLIMATE] = TuyaLocalClimate(device, ecfg)

    async_add_entities([data[CONF_CLIMATE]])
    _LOGGER.debug(f"Adding climate device for {discovery_info[CONF_TYPE]}")


async def async_setup_entry(hass, config_entry, async_add_entities):
    config = {**config_entry.data, **config_entry.options}
    discovery_info = {
        CONF_DEVICE_ID: config[CONF_DEVICE_ID],
        CONF_TYPE: config[CONF_TYPE],
    }
    await async_setup_platform(hass, {}, async_add_entities, discovery_info)
