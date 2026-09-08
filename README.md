## DictParser

DictParser is a typed utility to read configuration values from dictionaries, JSON files, and YAML files with support for dynamic placeholders.

### Features

- Dot-path access for nested dictionaries and lists
- Runtime placeholder resolution with `{key}` syntax
- Recursive resolution for nested containers (`dict`, `list`, `tuple`, `set`)
- Optional shallow copy for mutable return values
- Full resolved export with `get_all()`
- JSON/YAML serialization helpers: `to_json()` and `to_yaml()`
- File export helper with format inference: `save()`
- Runtime base folder management (`folder`) for relative include/update paths
- Include and update support with deep merge precedence control
- Dictionary-like API (`[]`, `in`, `len`, `del`, `pop`, `popitem`, `items`, `keys`, `values`)

### Installation

Install from source:

```bash
pip install -e .
```

### Quick Example

```python
from dictparser import DictParser

data = {
    "aa": "and",
    "c": [0, 1, "{a.c.d}"],
    "a": {"b": 1, "c": {"d": "{aa}", "e": "{a.b}"}},
}

parser = DictParser(data)

assert parser.get("a.b") == 1
assert parser.get("a.c.d") == "and"
assert parser.get("a.c.e") == "1"
assert parser.get("c.1") == 1
assert parser.get("c.2") == "and"
```

### Runtime Folder

`DictParser` computes `folder` at runtime:

- input is a `dict`: `folder` defaults to current working directory
- input is a file path: `folder` defaults to the file parent directory
- you can force it explicitly from init

```python
parser = DictParser({"a": 1})
parser = DictParser("params.json")
parser = DictParser({"a": 1}, folder="/tmp/configs")
```

### Include and Update

`include(...)` and `update(...)` accept:

- `str | Path` file paths (json/yaml)
- `dict[str, Any]`
- lists mixing the previous source types

`include(...)`: loads new params as defaults, then keeps current params precedence.

`update(...)`: inverse behavior, new params override current params.

```python
parser = DictParser({"db": {"host": "prod"}})
parser.include({"db": {"host": "default", "user": "app"}})
assert parser.get("db.host") == "prod"
assert parser.get("db.user") == "app"

parser.update({"db": {"host": "override"}})
assert parser.get("db.host") == "override"
```

### Dictionary-Like Helpers

```python
parser = DictParser({"a": {"b": 1}})

parser["a.c"] = 2
assert parser["a.c"] == 2
assert "a.b" in parser
assert len(parser) == 1  # top-level length

parser.setdefault("a.d", 3)
parser.pop("a.d")

# Deep traversal variants
parser.keys(deep=True)
parser.items(deep=True)
parser.values(deep=True)
```

### Notes on Resolution Dispatch

The resolver internally dispatches by container type while navigating paths:

- dictionary key lookup for mappings
- integer index lookup for lists and tuples
- recursive placeholder expansion for nested containers

This behavior is now documented directly in source comments in `src/dictparser/dictparser.py`.

### API Additions

The class exposes additional helpers for full output and persistence:

```python
resolved = parser.get_all()
json_text = parser.to_json()
yaml_text = parser.to_yaml()

# Infer format from output suffix (.json/.yaml/.yml), fallback json.
parser.save("output.json")
parser.save("output.yaml")

# Force format regardless of output suffix.
parser.save("output.txt", format="json")
parser.save("output.txt", format="yaml")
```

### CLI Usage

The package exposes a CLI entry point:

```bash
dictparser INPUT_FILE [-k KEY] [-o OUTPUT_FILE] [-f {json,yaml}]
```

- Without `-k/--key`, the CLI resolves and returns the entire dictionary (`get_all`).
- With `-k/--key`, the CLI resolves and returns only the selected key (`get`).
- With `-o/--output`, the CLI saves the result to file.
- With `-f/--format`, the output format is forced.
- Without `-f/--format`, format is inferred from output filename and defaults to json.

### Third-Party Licenses

Third-party licenses are archived in:

- `licenses/third_party/packages/`

Dependency summary and source links are listed in:

- `licenses/third_party/summary.tsv`
- `THIRD_PARTY_NOTICES.md`
