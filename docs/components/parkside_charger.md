# Parkside Charger (hub)

The `parkside_charger` component is the hub of a multi-slot charger for Parkside X20V (20 V,
5-cell Li-ion) battery packs. It owns the charging **power budget** of the power supply and
shares it between the slots, switches the 24 V supply to the slot boards, stops all charging when
the enclosure gets too hot, and reports totals for the whole charger.

Each battery slot is a separate [`parkside_slot`](parkside_slot.md) component (one LTC4162-L
charger per slot). The slots register themselves with the hub; the hub decides every update
interval which slot may charge, and with how much current.

```yaml
# Example configuration entry
external_components:
  - source:
      type: local
      path: components
    components: [parkside_charger, parkside_slot]

parkside_charger:
  id: charger
  max_total_current: 7A
  enable_output: bus_switch
  ambient_temperature: enclosure_temp
  total_input_power:
    name: "Total charging power"
  charging_count:
    name: "Batteries charging"
  present_count:
    name: "Batteries present"
  status:
    name: "Charger status"
```

## Configuration variables

- **id** (*Optional*, [ID](https://esphome.io/guides/configuration-types#config-id)): Manually
  specify the ID used for code generation and for `lambda` calls. Each `parkside_slot` refers to
  it with `charger_id` (only needed when there is more than one hub).
- **max_total_current** (*Optional*, current): The battery-side charge current shared by all
  slots, in amps. Size it to the power supply: about 21 V per amp plus 6 % charger loss.
  Range 0.3–60 A. Defaults to `8A`. Mean Well LOP-300-24: `7A` by convection, `10A` with a fan;
  LOP-400-24: `10A` / `13A`. Can be changed at run time (see [Lambda calls](#lambda-calls)).
- **enable_output** (*Optional*, [ID](https://esphome.io/guides/configuration-types#config-id)
  of a [binary output](https://esphome.io/components/output/)): Switches the 24 V supply of all
  slot boards. Turned on at boot and off whenever charging is disabled, the enclosure is too hot
  or the safety interlock is active.
- **ambient_temperature** (*Optional*, [ID](https://esphome.io/guides/configuration-types#config-id)
  of a [sensor](https://esphome.io/components/sensor/)): The temperature inside the enclosure.
  Without it, the over-temperature stop below is not available.
- **max_ambient_temperature** (*Optional*, float): Above this temperature in °C all charging stops
  and `enable_output` turns off. Charging resumes 3 °C below it. Range 20–70. Defaults to `45`.
- **storage_after_days** (*Optional*, float): In the slots' *Auto* mode, a pack that has not been
  touched for this many days is brought down from the ready level to the storage level.
  `0` = never. Range 0–45. Defaults to `14`.
- **storage_after_days_number** (*Optional*, [ID](https://esphome.io/guides/configuration-types#config-id)
  of a [number](https://esphome.io/components/number/)): Takes `storage_after_days` from a number
  entity instead, so it can be set in Home Assistant.
- **total_input_power** (*Optional*): Sum of the input power of all slots, in W. All options from
  [Sensor](https://esphome.io/components/sensor/).
- **charging_count** (*Optional*): Number of slots charging right now. All options from
  [Sensor](https://esphome.io/components/sensor/).
- **present_count** (*Optional*): Number of slots with a battery. All options from
  [Sensor](https://esphome.io/components/sensor/).
- **status** (*Optional*): The charger's state as text: `Charging 3 of 5`, `Idle, 5 batteries`,
  `Disabled`, `Stopped: enclosure too hot` or `Stopped: <reason>` (safety interlock). All options
  from [Text Sensor](https://esphome.io/components/text_sensor/).
- **update_interval** (*Optional*, [Time](https://esphome.io/guides/configuration-types#config-time)):
  How often the power budget is shared out and the totals are published. Defaults to `2s`.

The component needs the [I²C bus](https://esphome.io/components/i2c) (the slots use it).

## How the budget is shared

Every update interval the hub collects the slots that want to charge and serves them in order of
priority until `max_total_current` is used up:

1. slots with a *charge to 100 %* request,
2. then the emptiest packs first.

Each slot asks for its own maximum charge current (set per slot, and at most 1C when the pack's
nominal capacity is known). A pack in its constant-voltage phase only reserves what it actually
draws plus 0.3 A, so the next pack can start sooner. Allocations are rounded down to the
LTC4162's 0.1 A steps; a slot gets nothing rather than less than 0.3 A (unless it only asks for a
balancing tail). Slots that get nothing show *Waiting for power budget*.

## Lambda calls

From [lambdas](https://esphome.io/automations/templates#config-lambda), you can call these
methods on the hub (`id(charger)`):

- `set_enabled(bool enabled)`: Enables or disables charging on all slots, typically from a
  template switch:

  ```yaml
  switch:
    - platform: template
      name: "Charging enabled"
      optimistic: true
      restore_mode: RESTORE_DEFAULT_ON
      turn_on_action:
        - lambda: id(charger).set_enabled(true);
      turn_off_action:
        - lambda: id(charger).set_enabled(false);
  ```

- `set_interlock(bool active, std::string reason)`: A safety interlock, independent of
  `set_enabled()`. While it is active no slot charges and `enable_output` is off, whatever the
  enable switch says; it acts at once, without waiting for the next update. The reason shows in
  `status` as `Stopped: <reason>`. Call it again with `false` to release it.
- `set_max_total_current(float amps)`: Changes the budget at run time, for example when a fan on
  the power supply is confirmed running. Takes effect at the next update.
- `request_full_all()`: Asks every slot to charge to 100 % (and run a balancing tail), as the
  slot's own *charge to 100 %* does.
- `is_enabled()`: `true` while charging is allowed (enabled, not too hot, no interlock).
- `slots()`: The registered slots, for example to check for faults:

  ```yaml
  interval:
    - interval: 10s
      then:
        - lambda: |-
            bool fault = false;
            for (auto *s : id(charger)->slots())
              fault |= s->phase() == esphome::parkside_charger::Phase::FAULT;
            id(buzzer).set_state(fault);
  ```

## Example: safety interlock

Stops charging while the enclosure or the room is too hot, or while Home Assistant is
unreachable (abridged from `parkside-charger.yaml`):

```yaml
sensor:
  - platform: homeassistant
    id: room_temp
    entity_id: sensor.hotpress_temperature_sensor_temperature
    internal: true

interval:
  - interval: 5s
    then:
      - lambda: |-
          std::vector<std::string> why;
          if (id(enclosure_temp).state > 45) why.push_back("enclosure too hot");
          if (std::isnan(id(room_temp).state) || id(room_temp).state > 36) why.push_back("room too hot");
          if (!api::global_api_server->is_connected()) why.push_back("Home Assistant not connected");
          std::string reason;
          for (auto &w : why) reason += (reason.empty() ? "" : ", ") + w;
          id(charger).set_interlock(!why.empty(), reason);
```

The full version adds hysteresis, a grace period and a switch to allow charging without Home
Assistant.

## See also

- [Parkside Slot](parkside_slot.md)
- [Firmware overview](../firmware.md): charging strategy, LED legend, safety interlock, PSU fan
- [I²C Bus](https://esphome.io/components/i2c), [TCA9548A I²C Multiplexer](https://esphome.io/components/tca9548a)
