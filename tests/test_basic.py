from dictparser import DictParser
from typing import Any
import json


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
