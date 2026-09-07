# Library

## Main Class

The main entry point is `DictParser`.

```python
from dictparser import DictParser
```

## Input Sources

You can initialize `DictParser` with:

- `dict[str, Any]`
- `str` path to a JSON/YAML file
- `pathlib.Path` to a JSON/YAML file

## Path Resolution

Use dot-separated paths:

```python
value = parser.get("a.b.c")
```

For sequences, indices are resolved as strings:

```python
value = parser.get("items.0")
```

## Placeholder Resolution

String values can reference other keys:

```python
{"name": "alice", "greeting": "hello {name}"}
```

`parser.get("greeting")` returns `"hello alice"`.

Resolution is recursive for container types (`dict`, `list`, `tuple`, `set`).

## Mutable Return Values

`get(..., copy=True)` returns a shallow copy for `dict` and `list` values to avoid unintended mutations.
