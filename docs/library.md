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

Optional init argument:

- `folder: str | Path | None`

If not provided:

- dict input => `folder` is current working directory
- file input => `folder` is file parent directory

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

## Include and Update

`include(...)` and `update(...)` accept:

- a file path (`str | Path`)
- a dictionary (`dict[str, Any]`)
- a list mixing file paths and dictionaries

`include(...)` applies deep merge using loaded params as defaults and keeping current params precedence.

`update(...)` applies deep merge with inverse precedence, so loaded params override current params.

## Dictionary-Like API

`DictParser` supports dictionary-like operations for path-based access and mutation:

- `__getitem__`, `__setitem__`, `__delitem__`, `__contains__`
- `__iter__`, `__len__`
- `set`, `setdefault`, `delete`, `pop`, `popitem`
- `clear`, `copy`, `contains`, `has_key`
- `items(deep=False)`, `keys(deep=False)`, `values(deep=False)`

When `deep=True`, `items/keys/values` traverse nested dictionaries/lists and expose dot-path keys.
