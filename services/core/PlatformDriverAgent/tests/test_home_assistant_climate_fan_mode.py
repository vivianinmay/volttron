# -*- coding: utf-8 -*- {{{
# ===----------------------------------------------------------------------===
#
#                 Component of Eclipse VOLTTRON
#
# ===----------------------------------------------------------------------===
# }} }

import pytest
from unittest.mock import patch

from platform_driver.interfaces.home_assistant import Interface, HomeAssistantRegister


@pytest.fixture
def climate_interface():
    return Interface()


def _insert_climate_fan_mode_register(interface, point_name="fan_mode", read_only=False, reg_type=str):
    register = HomeAssistantRegister(
        read_only=read_only,
        pointName=point_name,
        units="",
        reg_type=reg_type,
        attributes={},
        entity_id="climate.living_room",
        entity_point="fan_mode",
        default_value=None,
        description="test climate fan_mode register",
    )
    interface.insert_register(register)
    return register


# 1. test scrape_all reads fan_mode from climate attributes
@patch.object(Interface, "get_entity_data")
def test_scrape_all_reads_climate_fan_mode(mock_get_entity_data, climate_interface):
    _insert_climate_fan_mode_register(climate_interface, read_only=True)
    mock_get_entity_data.return_value = {
        "state": "cool",
        "attributes": {"fan_mode": "medium"},
    }

    result = climate_interface._scrape_all()

    assert result["fan_mode"] == "medium"


# 2. test _set_point routing for fan_mode should call helper
@patch.object(Interface, "set_fan_mode")
def test_set_point_fan_mode_routes_to_helper(set_fan_mode_mock, climate_interface):
    _insert_climate_fan_mode_register(climate_interface, read_only=False)

    returned = climate_interface._set_point("fan_mode", "low")

    assert returned == "low"
    set_fan_mode_mock.assert_called_once_with(entity_id="climate.living_room", fan_mode="low")


# 3. test set_fan_mode helper sends correct HA API request
@patch("platform_driver.interfaces.home_assistant._post_method")
def test_set_fan_mode_api_call(post_mock, climate_interface):
    climate_interface.ip_address = "127.0.0.1"
    climate_interface.port = 8123
    climate_interface.access_token = "token"

    climate_interface.set_fan_mode("climate.living_room", "high")

    (url, headers, data, operation_description), _ = post_mock.call_args
    assert url.endswith("/api/services/climate/set_fan_mode")
    assert data == {
        "entity_id": "climate.living_room",
        "fan_mode": "high",
    }
    assert operation_description == "set fan mode of climate.living_room to high"
