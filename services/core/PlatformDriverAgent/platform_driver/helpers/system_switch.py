# -*- coding: utf-8 -*-

from volttron.platform.agent.known_identities import PLATFORM_DRIVER


class SystemSwitchController:
    """System-level switch coordinator using PlatformDriverAgent RPC set_point calls."""

    def __init__(self, rpc_agent, device_map, default_states=None, timeout=20):
        self._rpc_agent = rpc_agent
        self._device_map = device_map or {}
        self._default_states = default_states or {}
        self._timeout = timeout

    def _set_point(self, driver_name, point_name, value):
        return self._rpc_agent.vip.rpc.call(
            PLATFORM_DRIVER,
            "set_point",
            driver_name,
            point_name,
            value,
        ).get(timeout=self._timeout)

    def system_switch_off(self):
        # turn off lights
        for entry in self._device_map.get("lights", []):
            self._set_point(entry["driver"], entry["point"], 0)

        # set HVAC mode to OFF (existing home_assistant mapping: off=0)
        for entry in self._device_map.get("hvac", []):
            self._set_point(entry["driver"], entry["point"], 0)

        # lock doors (lock mapping: locked=1)
        for entry in self._device_map.get("locks", []):
            self._set_point(entry["driver"], entry["point"], 1)

    def system_switch_on(self):
        # restore devices to default states
        for entry in self._device_map.get("lights", []):
            value = self._default_states.get("lights", {}).get(entry["point"], 1)
            self._set_point(entry["driver"], entry["point"], value)

        for entry in self._device_map.get("hvac", []):
            value = self._default_states.get("hvac", {}).get(entry["point"], 4)
            self._set_point(entry["driver"], entry["point"], value)

        for entry in self._device_map.get("locks", []):
            value = self._default_states.get("locks", {}).get(entry["point"], 0)
            self._set_point(entry["driver"], entry["point"], value)
