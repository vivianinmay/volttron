# -*- coding: utf-8 -*-

import pytest

from volttron.platform.agent.known_identities import PLATFORM_DRIVER
from platform_driver.helpers.system_switch import SystemSwitchController

# mock objects , since we want to test the controller logic without needing a full Volttron instance or real RPC calls

class _DummyFuture:
    def __init__(self, value=None):
        self._value = value

    def get(self, timeout=None):
        return self._value


class _DummyRPC:  # Remote Procedure Call
    def __init__(self):
        self.calls = []

    def call(self, peer, method, driver_name, point_name, value):
        self.calls.append((peer, method, driver_name, point_name, value))
        return _DummyFuture(value)


class _DummyVIP:  # Volttron Interconnect Protocol
    def __init__(self):
        self.rpc = _DummyRPC()


class _DummyAgent:
    def __init__(self):
        self.vip = _DummyVIP()


def test_system_switch_off_calls_platform_driver_set_point_in_order():
    agent = _DummyAgent()
    controller = SystemSwitchController(
        rpc_agent=agent,
        device_map={
            "lights": [{"driver": "home_assistant", "point": "bool_state"}],
            "hvac": [{"driver": "home_assistant", "point": "climate_state"}],
            "locks": [{"driver": "home_assistant", "point": "lock_state"}],
        },
    )

    controller.system_switch_off()

    assert agent.vip.rpc.calls == [
        (PLATFORM_DRIVER, "set_point", "home_assistant", "bool_state", 0),
        (PLATFORM_DRIVER, "set_point", "home_assistant", "climate_state", 0),
        (PLATFORM_DRIVER, "set_point", "home_assistant", "lock_state", 1),
    ]


def test_system_switch_on_restores_defaults():
    agent = _DummyAgent()
    controller = SystemSwitchController(
        rpc_agent=agent,
        device_map={
            "lights": [{"driver": "home_assistant", "point": "bool_state"}],
            "hvac": [{"driver": "home_assistant", "point": "climate_state"}],
            "locks": [{"driver": "home_assistant", "point": "lock_state"}],
        },
        default_states={
            "lights": {"bool_state": 1},
            "hvac": {"climate_state": 4},
            "locks": {"lock_state": 0},
        },
    )

    controller.system_switch_on()

    assert agent.vip.rpc.calls == [
        (PLATFORM_DRIVER, "set_point", "home_assistant", "bool_state", 1),
        (PLATFORM_DRIVER, "set_point", "home_assistant", "climate_state", 4),
        (PLATFORM_DRIVER, "set_point", "home_assistant", "lock_state", 0),
    ]


def test_system_switch_on_uses_fallback_defaults_when_missing():
    agent = _DummyAgent()
    controller = SystemSwitchController(
        rpc_agent=agent,
        device_map={
            "lights": [{"driver": "home_assistant", "point": "bool_state"}],
            "hvac": [{"driver": "home_assistant", "point": "climate_state"}],
            "locks": [{"driver": "home_assistant", "point": "lock_state"}],
        },
        default_states={},
    )

    controller.system_switch_on()

    assert agent.vip.rpc.calls == [
        (PLATFORM_DRIVER, "set_point", "home_assistant", "bool_state", 1),
        (PLATFORM_DRIVER, "set_point", "home_assistant", "climate_state", 4),
        (PLATFORM_DRIVER, "set_point", "home_assistant", "lock_state", 0),
    ]
