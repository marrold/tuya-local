"""
Config parser for Tuya Local devices.
"""
import logging

from os import walk
from os.path import join, dirname
from fnmatch import fnmatch
from homeassistant.util.yaml import load_yaml

import custom_components.tuya_local.devices

_CONFIG_DIR = dirname(custom_components.tuya_local.devices.__file__)
_LOGGER = logging.getLogger("tuya_local")


def _typematch(type, value):
    if isinstance(value, type):
        return True
    # Allow values embedded in strings if they can be converted
    # But not for bool, as everything can be converted to bool
    elif isinstance(value, str) and type is not bool:
        try:
            type(value)
            return True
        except ValueError:
            return False
    return False


class TuyaDeviceConfig:
    """Representation of a device config for Tuya Local devices."""

    def __init__(self, fname):
        """Initialize the device config.
        Args:
            fname (string): The filename of the yaml config to load."""
        self.__fname = fname
        filename = join(_CONFIG_DIR, fname)
        self.__config = load_yaml(filename)
        _LOGGER.debug("Loaded device config %s", fname)

    @property
    def name(self):
        """Return the friendly name for this device."""
        return self.__config["name"]

    @property
    def primary_entity(self):
        """Return the primary type of entity for this device."""
        return TuyaEntityConfig(self, self.__config["primary_entity"])

    def secondary_entities(self):
        """Iterate through entites for any secondary entites supported."""
        if "secondary_entities" in self.__config.keys():
            for conf in self.__config["secondary_entities"]:
                yield TuyaEntityConfig(self, conf)

    def matches(self, dps):
        """Determine if this device matches the provided dps map."""
        for d in self.primary_entity.dps():
            if d.id not in dps.keys() or not _typematch(d.type, dps[d.id]):
                return False

        for dev in self.secondary_entities():
            for d in dev.dps():
                if d.id not in dps.keys() or not _typematch(d.type, dps[d.id]):
                    return False
        _LOGGER.debug("Matched config for %s", self.name)
        return True


class TuyaEntityConfig:
    """Representation of an entity config for a supported entity."""

    def __init__(self, device, config):
        self.__device = device
        self.__config = config

    @property
    def name(self):
        """The friendly name for this entity."""
        if "name" in self.__config:
            return self.__config["name"]
        else:
            return self.__device.name

    @property
    def legacy_device(self):
        """Return the legacy device corresponding to this config."""
        if "legacy_class" in self.__config:
            return self.__config["legacy_class"]
        else:
            return None

    @property
    def entity(self):
        """The entity type of this entity."""
        return self.__config["entity"]

    def dps(self):
        """Iterate through the list of dps for this entity."""
        for d in self.__config["dps"]:
            yield TuyaDpsConfig(self, d)


class TuyaDpsConfig:
    """Representation of a dps config."""

    def __init__(self, entity, config):
        self.__entity = entity
        self.__config = config

    @property
    def id(self):
        return str(self.__config["id"])

    @property
    def type(self):
        t = self.__config["type"]
        types = {
            "boolean": bool,
            "integer": int,
            "string": str,
            "float": float,
            "bitfield": int,
        }
        return types.get(t, None)

    @property
    def name(self):
        return self.__config["name"]

    @property
    def isreadonly(self):
        return "readonly" in self.__config.keys() and self.__config["readonly"] is True

    @property
    def map_from_dps(self, value):
        result = value
        if "mapping" in self.__config.keys():
            for map in self.__config["mapping"]:
                if map["dps_val"] == value and "value" in map:
                    result = map["value"]
                    _LOGGER.debug(
                        "%s: Mapped dps %d value from %s to %s",
                        self.__entity.__device.name,
                        self.id,
                        value,
                        result,
                    )
        return result

    @property
    def map_to_dps(self, value):
        result = value
        if "mapping" in self.__config.keys():
            for map in self.__config["mapping"]:
                if "value" in map and map["value"] == value:
                    result = map["dps_val"]
                    _LOGGER.debug(
                        "%s: Mapped dps %d to %s from %s",
                        self.__entity.__device.name,
                        self.id,
                        result,
                        value,
                    )
        return result


def available_configs():
    """List the available config files."""
    for (path, dirs, files) in walk(_CONFIG_DIR):
        for basename in sorted(files):
            if fnmatch(basename, "*.yaml"):
                yield basename