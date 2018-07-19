# Burler

> **def.** [[1]](https://www.merriam-webster.com/dictionary/burler) plural -s
> 1 : one that removes loose threads, knots, and other imperfections from cloth

A library to help write taps in accordance with the [Singer specification](https://github.com/singer-io/getting-started).


# Features
- **Config file validation** `tap = Tap(config_spec=spec)` - Burler supports the following methods of validating config:
  - List Key-based inference - Takes a provided `list` of required keys and ensures that they are present
  - Dict Key-based inference - Takes a provided `dict` and validates that *ALL* its keys are present at runtime (no optional config support)
  - [Voluptuous](https://github.com/alecthomas/voluptuous) Schema - Validates according to a voluptuous Schema object
  - [schema](https://github.com/keleshev/schema) - Validates according to a schema Schema object
  - (Coming Soon) Example Config File - Same as key-based inference, but a relative file path can be specified instead of a dict object
