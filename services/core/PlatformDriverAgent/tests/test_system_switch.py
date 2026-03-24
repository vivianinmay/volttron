# -*- coding: utf-8 -*-

import pytest
from unittest.mock import MagicMock, call

from volttron.platform.agent.known_identities import PLATFORM_DRIVER
from platform_driver.helpers.system_switch import SystemSwitchController


class DummyRPC:
    def __init__(self):
        self.call = MagicMock()
        # Ensure that whatever call() returns has a .get() method that returns None
        self.call.return_value.get.return_value = None


class DummyVIP:
    def __init__(self):
        self.rpc = DummyRPC()


class DummyAgent:
    """Mock agent to simulate VOLTTRON agent with VIP RPC capabilities."""
    def __init__(self):
        self.vip = DummyVIP()


@pytest.fixture
def dummy_agent():
    return DummyAgent()


@pytest.fixture
def device_map():
    return {
        "lights": [
            {"driver": "home_assistant_1", "point": "living_room_light"},
            {"driver": "home_assistant_1", "point": "kitchen_light"}
        ],
        "hvac": [
            {"driver": "home_assistant_2", "point": "thermostat_mode"}
        ],
        "locks": [
            {"driver": "home_assistant_1", "point": "front_door_lock"}
        ]
    }


@pytest.fixture
def default_states():
    return {
        "lights": {
            "living_room_light": 1,
            "kitchen_light": 1
        },
        "hvac": {
            "thermostat_mode": 4  # 4 = auto
        },
        "locks": {
            "front_door_lock": 0  # 0 = unlocked
        }
    }


@pytest.fixture
def switch_controller(dummy_agent, device_map, default_states):
    return SystemSwitchController(
        rpc_agent=dummy_agent,
        device_map=device_map,
        default_states=default_states,
        timeout=10
    )


def test_system_switch_off_sets_correct_values(switch_controller, dummy_agent):
    """
    Test that switching off the system correctly turns off lights,
    sets HVAC to off (0), and locks the doors (1) via PlatformDriver set_point RPC.
    """
    switch_controller.system_switch_off()

    # Verify RPC calls were made in the expected order with correct parameters
    expected_calls = [
        # Lights off
        call(PLATFORM_DRIVER, "set_point", "home_assistant_1", "living_room_light", 0),
        call().get(timeout=10),
        call(PLATFORM_DRIVER, "set_point", "home_assistant_1", "kitchen_light", 0),
        call().get(timeout=10),
        # HVAC off (0)
        call(PLATFORM_DRIVER, "set_point", "home_assistant_2", "thermostat_mode", 0),
        call().get(timeout=10),
        # Locks locked (1)
        call(PLATFORM_DRIVER, "set_point", "home_assistant_1", "front_door_lock", 1),
        call().get(timeout=10),
    ]

    dummy_agent.vip.rpc.call.assert_has_calls(expected_calls, any_order=False)
    assert dummy_agent.vip.rpc.call.call_count == 4


def test_system_switch_on_restores_default_states(switch_controller, dummy_agent):
    """
    Test that switching on the system restores states based on the provided default_states.
    """
    switch_controller.system_switch_on()

    expected_calls = [
        # Lights restored to 1
        call(PLATFORM_DRIVER, "set_point", "home_assistant_1", "living_room_light", 1),
        call().get(timeout=10),
        call(PLATFORM_DRIVER, "set_point", "home_assistant_1", "kitchen_light", 1),
        call().get(timeout=10),
        # HVAC restored to 4 (auto)
        call(PLATFORM_DRIVER, "set_point", "home_assistant_2", "thermostat_mode", 4),
        call().get(timeout=10),
        # Locks restored to 0 (unlocked)
        call(PLATFORM_DRIVER, "set_point", "home_assistant_1", "front_door_lock", 0),
        call().get(timeout=10),
    ]

    dummy_agent.vip.rpc.call.assert_has_calls(expected_calls, any_order=False)
    assert dummy_agent.vip.rpc.call.call_count == 4


def test_system_switch_on_uses_fallback_defaults(dummy_agent, device_map):
    """
    Test that switching on the system uses fallback values if default_states is empty.
    Fallbacks: lights = 1, hvac = 4, locks = 0.
    """
    controller = SystemSwitchController(
        rpc_agent=dummy_agent,
        device_map=device_map,
        default_states={},  # Empty defaults to test fallback
        timeout=15
    )

    controller.system_switch_on()

    expected_calls = [
        call(PLATFORM_DRIVER, "set_point", "home_assistant_1", "living_room_light", 1),
        call().get(timeout=15),
        call(PLATFORM_DRIVER, "set_point", "home_assistant_1", "kitchen_light", 1),
        call().get(timeout=15),
        call(PLATFORM_DRIVER, "set_point", "home_assistant_2", "thermostat_mode", 4),
        call().get(timeout=15),
        call(PLATFORM_DRIVER, "set_point", "home_assistant_1", "front_door_lock", 0),
        call().get(timeout=15),
    ]

    dummy_agent.vip.rpc.call.assert_has_calls(expected_calls, any_order=False)
