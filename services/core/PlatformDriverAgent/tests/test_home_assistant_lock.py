# -*- coding: utf-8 -*- {{{
# ===----------------------------------------------------------------------===
#
#                 Component of Eclipse VOLTTRON
#
# ===----------------------------------------------------------------------===
# }} }

import pytest
from unittest.mock import patch

from platform_driver.interfaces.home_assistant import Interface, HomeAssistantRegister # Interface is the class we're testing, HomeAssistantRegister is used to create test registers for the lock state

#每次运行一个 test method 时，pytest 会自动创建一个新的 Interface() 对象，并把它传给这个 test method 使用,防止一个 test 的状态影响另一个 test.
# every time a test method is run, pytest will automatically create a new Interface() object and pass it to the test method to use. 
# This ensures that each test runs with a fresh instance of the interface, preventing state from one test affecting another.
#在测试开始前自动准备一些对象或环境。如果 test function 的参数名是：lock_interface，那么 pytest 会调用这个 lock_interface() 函数来创建一个 Interface 实例，并把它传给 test function 使用。
# 不用每个test function 里都写一遍 interface = Interface()的创建代码了。
@pytest.fixture 
def lock_interface():
    return Interface()


# Helper function to insert a lock register into the interface for testing
def _insert_lock_register(interface, point_name="lock_state", read_only=False, reg_type=int):
    register = HomeAssistantRegister(
        read_only=read_only,
        pointName=point_name,
        units="",
        reg_type=reg_type,
        attributes={},
        entity_id="lock.front_door",
        entity_point="state",
        default_value=None,
        description="test lock register",
    )
    interface.insert_register(register)
    return register


# 1. test  when HA lock state is "locked", the scrape_all method should map it to 1    
def test_scrape_all_lock_locked_maps_to_1(lock_interface):
    _insert_lock_register(lock_interface, read_only=True)

    with patch.object(Interface, "get_entity_data", return_value={"state": "locked", "attributes": {}}):
        result = lock_interface._scrape_all()

    assert result["lock_state"] == 1

# 2. test when HA lock state is "unlocked", the scrape_all method should map it to 0
def test_scrape_all_lock_unlocked_maps_to_0(lock_interface):
    _insert_lock_register(lock_interface, read_only=True)

    with patch.object(Interface, "get_entity_data", return_value={"state": "unlocked", "attributes": {}}):
        result = lock_interface._scrape_all()

    assert result["lock_state"] == 0

# 3. test when HA lock state is unknown, the scrape_all method should fall back to 0 and not raise an error
# if the state is something other than "locked" or "unlocked", we should default to 0 (unlocked) to avoid potential safety issues.
# This test ensures that the code handles unexpected states gracefully without crashing.
def test_scrape_all_lock_unknown_state_falls_back_safely(lock_interface):
    _insert_lock_register(lock_interface, read_only=True)

    with patch.object(Interface, "get_entity_data", return_value={"state": "locking", "attributes": {}}):
        result = lock_interface._scrape_all()

    assert result["lock_state"] == 0

# 4. test that setting lock_state to 1 calls lock_device
def test_set_point_lock_value_1_calls_lock_device(lock_interface):
    _insert_lock_register(lock_interface, read_only=False)

    with patch.object(Interface, "lock_device") as lock_mock, patch.object(Interface, "unlock_device") as unlock_mock:
        returned = lock_interface._set_point("lock_state", 1)

    assert returned == 1
    lock_mock.assert_called_once_with("lock.front_door")
    unlock_mock.assert_not_called()

# 5. test that setting lock_state to 0 calls unlock_device
def test_set_point_lock_value_0_calls_unlock_device(lock_interface):
    _insert_lock_register(lock_interface, read_only=False)

    with patch.object(Interface, "lock_device") as lock_mock, patch.object(Interface, "unlock_device") as unlock_mock:
        returned = lock_interface._set_point("lock_state", 0)

    assert returned == 0
    unlock_mock.assert_called_once_with("lock.front_door")
    lock_mock.assert_not_called()

# 6. test that setting lock_state to an invalid value raises ValueError
def test_set_point_lock_rejects_invalid_value(lock_interface):
    _insert_lock_register(lock_interface, read_only=False)

    with pytest.raises(ValueError):
        lock_interface._set_point("lock_state", 2)


# 7. test that lock_device makes the correct API call to HA
# @patch is used to mock the _post_method which is responsible for making HTTP POST requests to HA. not actually sending requests to HA.
@patch("platform_driver.interfaces.home_assistant._post_method")
def test_lock_device_calls_lock_service(post_mock, lock_interface):
    lock_interface.ip_address = "127.0.0.1"
    lock_interface.port = 8123
    lock_interface.access_token = "token"

    lock_interface.lock_device("lock.front_door")

    (url, headers, data, operation_description), _ = post_mock.call_args
    assert url.endswith("/api/services/lock/lock")
    assert data["entity_id"] == "lock.front_door"
    assert "lock lock.front_door" == operation_description

# 8. test that unlock_device makes the correct API call to HA
@patch("platform_driver.interfaces.home_assistant._post_method")
def test_unlock_device_calls_unlock_service(post_mock, lock_interface):
    lock_interface.ip_address = "127.0.0.1"
    lock_interface.port = 8123
    lock_interface.access_token = "token"

    lock_interface.unlock_device("lock.front_door")

    (url, headers, data, operation_description), _ = post_mock.call_args
    assert url.endswith("/api/services/lock/unlock")
    assert data["entity_id"] == "lock.front_door"
    assert "unlock lock.front_door" == operation_description
