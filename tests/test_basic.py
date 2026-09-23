from dictparser import DictParser
from typing import Any
import json
from pathlib import Path


def test_get_param():
    data: dict[str, Any] = {"aa": "and", "c": [0, 1, "{a.c.d}"], "a": {"b": 1, "c": {"d": "{aa}", "e": "{a.b}"}}}
    parser = DictParser(data)
    assert parser.get("a.b") == 1
    assert parser.get("a.c.d") == "and"
    assert parser.get("a.c.e") == "1"
    assert parser.get("c.1") == 1
    assert parser.get("c.2") == "and"


def test_load_from_json_file(tmp_path: Any):
    data: dict[str, Any] = {
        "name": "world",
        "a": {"b": 7, "msg": "hello {name}"},
        "items": ["x", "{a.b}"],
    }
    file_path = tmp_path / "params.json"
    file_path.write_text(json.dumps(data), encoding="utf-8")

    parser = DictParser(file_path)

    assert parser.get("a.b") == 7
    assert parser.get("a.msg") == "hello world"
    assert parser.get("items.1") == "7"


def test_load_from_yaml_file(tmp_path: Any):
    yaml_data = """
name: world
a:
    b: 7
    msg: hello {name}
items:
    - x
    - "{a.b}"
"""
    file_path = tmp_path / "params.yaml"
    file_path.write_text(yaml_data, encoding="utf-8")

    parser = DictParser(file_path)

    assert parser.get("a.b") == 7
    assert parser.get("a.msg") == "hello world"
    assert parser.get("items.1") == "7"


def test_get_all_resolves_entire_structure():
    data: dict[str, Any] = {
        "name": "world",
        "a": {"b": 7, "msg": "hello {name}"},
        "items": ["x", "{a.b}"],
    }
    parser = DictParser(data)

    assert parser.get_all() == {
        "name": "world",
        "a": {"b": 7, "msg": "hello world"},
        "items": ["x", "7"],
    }


def test_save_infers_format_from_output_name(tmp_path: Any):
    data: dict[str, Any] = {"value": "{nested.a}", "nested": {"a": 3}}
    parser = DictParser(data)

    json_out = tmp_path / "out.json"
    yaml_out = tmp_path / "out.yaml"

    parser.save(json_out)
    parser.save(yaml_out)

    assert json.loads(json_out.read_text(encoding="utf-8"))["value"] == "3"
    assert DictParser(yaml_out).get("value") == "3"


def test_folder_is_runtime_for_dict_and_file_and_can_be_forced(tmp_path: Any):
    parser_from_dict = DictParser({"a": 1})
    assert parser_from_dict.folder == Path.cwd().resolve()

    json_file = tmp_path / "params.json"
    json_file.write_text(json.dumps({"a": 1}), encoding="utf-8")
    parser_from_file = DictParser(json_file)
    assert parser_from_file.folder == tmp_path.resolve()

    forced = tmp_path / "forced"
    parser_forced = DictParser({"a": 1}, folder=forced)
    assert parser_forced.folder == forced.resolve()


def test_include_and_update_deep_merge_with_inverse_precedence(tmp_path: Any):
    parser = DictParser({"db": {"host": "prod", "port": 5432}, "a": 1})

    include_file = tmp_path / "defaults.json"
    include_file.write_text(
        json.dumps({"db": {"host": "default", "user": "app"}, "env": "dev"}),
        encoding="utf-8",
    )

    parser.include(include_file)
    assert parser.get("db.host") == "prod"
    assert parser.get("db.user") == "app"
    assert parser.get("env") == "dev"

    parser.update({"db": {"host": "override"}, "a": 2})
    assert parser.get("db.host") == "override"
    assert parser.get("a") == 2


def test_include_uses_folder_for_relative_paths(tmp_path: Any):
    params_file = tmp_path / "params.json"
    params_file.write_text(json.dumps({"current": 1}), encoding="utf-8")

    include_file = tmp_path / "extra.json"
    include_file.write_text(json.dumps({"extra": 7}), encoding="utf-8")

    parser = DictParser(params_file)
    parser.include("extra.json")
    assert parser.get("extra") == 7


def test_set_setdefault_mapping_like_helpers_and_deep_options() -> None:
    parser = DictParser({"a": {"b": 1}, "items": ["x"]})

    parser.set("a.c", "v")
    assert parser.get("a.c") == "v"

    parser["a.d"] = 5
    assert parser["a.d"] == 5

    value = parser.setdefault("a.d", 10)
    assert value == 5

    defaulted = parser.setdefault("a.e", 10)
    assert defaulted == 10
    assert parser.get("a.e") == 10

    assert "a.b" in parser
    assert parser.contains("b", deep=True)
    assert parser.has_key("e", deep=True)

    top_keys = parser.keys()
    assert "a" in top_keys
    deep_keys = parser.keys(deep=True)
    assert "a.b" in deep_keys

    top_items = dict(parser.items())
    assert "a" in top_items
    deep_items = dict(parser.items(deep=True))
    assert deep_items["a.b"] == 1

    popped = parser.pop("a.e")
    assert popped == 10
    assert parser.get("a.e", default="missing") == "missing"

    deep_key, deep_value = parser.popitem(deep=True)
    assert isinstance(deep_key, str)
    assert deep_value is not None

    parser["a.x"] = 99
    del parser["a.x"]
    assert parser.get("a.x", default=None) is None

    parsed_copy = parser.copy()
    assert isinstance(parsed_copy, dict)
    assert len(parser) >= 1

    parser.clear()
    assert len(parser) == 0
