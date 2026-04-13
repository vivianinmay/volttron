# Developer Guide: Adding New Home Assistant Entities to Volttron

## 1. Introduction

The Volttron Home Assistant Driver enables seamless integration between Volttron and Home Assistant (HA). Currently, the driver supports core entities such as `light`, `climate` (thermostats), `switch`, and `lock`.

Home Assistant supports over 40 different entity domains (e.g., `cover`, `media_player`, `vacuum`, `valve`, `sensor`, etc.). Because the underlying REST API logic for controlling these devices is highly standardized across Home Assistant, it is not necessary to hardcode every single device type from scratch. 

Instead, this guide provides a standardized, step-by-step process for developers to extend the Volttron driver to support **any** new Home Assistant entity domain. By following this pattern, you can easily add write-access (control) functionality for new devices.

## 2. Architecture Overview

Before adding a new entity, it is helpful to understand the data flow in the Volttron Home Assistant Driver:

1. **Reading States (`_scrape_all`)**: The driver polls Home Assistant, checks the `entity_id` domain (e.g., `lock.`), and maps the HA string state (e.g., "locked") to a Volttron numeric value (e.g., 1).
2. **Writing Commands (`_set_point`)**: A Volttron agent issues a command. The interface identifies the domain via `entity_id`, validates the input, and calls a specific action method.
3. **HTTP Requests (`_post_method`)**: The action method constructs the URL and payload, then uses the global `_post_method` to send a POST request to the Home Assistant REST API.

## 3. Step-by-Step Implementation Guide

### Step 1: Identify the HA Domain and Services
Consult the [Home Assistant Developer Documentation](https://developers.home-assistant.io/docs/core/entity/) to identify the **Domain** and **Services** for the entity you want to add.
*   *Example:* For a smart blind, the domain is `cover`. Services are `open_cover` and `close_cover`.

### Step 2: Update the Interface Routing (`home_assistant.py`)
Navigate to `platform_driver/interfaces/home_assistant.py`. You need to update two main areas:

**1. Reading States (`_scrape_all`):**
Locate the `_scrape_all` method. Add an `elif` branch to map the Home Assistant string state to a Volttron numeric value.

```python
# Inside _scrape_all(self):
elif "cover." in entity_id:
    if entity_point == "state":
        state = entity_data.get("state", None)
        if state == "open":
            register.value = 1
            result[register.point_name] = 1
        elif state == "closed":
            register.value = 0
            result[register.point_name] = 0
```

**2. Writing Commands (`_set_point`):**
Locate the `_set_point` method. Add a routing branch for your new entity domain.

```python
# Inside _set_point(self, point_name, value):
elif "cover." in register.entity_id:
    if entity_point == "state":
        if register.value in [0, 1]:
            if register.value == 1:
                self.open_cover(register.entity_id)
            else:
                self.close_cover(register.entity_id)
        else:
            raise ValueError(f"State value for {register.entity_id} should be 1 or 0")
```

**3. Create the Action Method:**
Create the corresponding method that uses the driver's `_post_method`:

```python
def open_cover(self, entity_id):
    url = f"http://{self.ip_address}:{self.port}/api/services/cover/open_cover"
    headers = {
        "Authorization": f"Bearer {self.access_token}",
        "Content-Type": "application/json",
    }
    payload = {"entity_id": entity_id}
    _post_method(url, headers, payload, f"open {entity_id}")
```

### Step 3: Update the Driver Registry Configuration
To allow Volttron to recognize the new device, users must define it in the driver's registry configuration file (`.csv`). 

**Example Registry Entry:**
```csv
Volttron Point Name, Home Assistant Entity ID, Type, Units, Writable
LivingRoom_Blinds, cover.living_room_blinds, int, None, TRUE
```

### Step 4: Write Unit Tests (Mandatory)
Every new entity must be accompanied by unit tests to prevent regressions. Create a new test file in `tests/` (e.g., `test_home_assistant_cover.py`) and mock the API responses.

*(Reference: See `test_home_assistant_lock.py` for a complete example of testing `_scrape_all` and `_set_point` logic).*

## 4. Supported Entity Roadmap

**Currently Supported:**
- [x] Light (`light`)
- [x] Climate / Thermostat (`climate`)
- [x] Switch (`switch`)
- [x] Lock (`lock`)
- [x] Fan (`fan`)

**Available for Future Contribution:**
- [ ] Cover (`cover` - Blinds, Garage doors)
- [ ] Media player (`media_player`)
- [ ] Vacuum (`vacuum`)
- [ ] Valve (`valve`)
- [ ] *...and many more.*
