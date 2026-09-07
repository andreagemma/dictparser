from pathlib import Path
from typing import Any
from string import Formatter
from typing import Hashable
import json


class DictParser:
    def __init__(self, params_or_path: dict[str, Any] | str | Path):
        assert isinstance(params_or_path, (dict, str, Path)), (
            "params_or_path must be a dict or a file path (str or Path)"
        )

        if isinstance(params_or_path, dict):
            self.params: dict[str, Any] = params_or_path
        else:
            self.params = self._load_params_from_file(params_or_path)

    def _load_params_from_file(self, file_path: str | Path) -> dict[str, Any]:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if file_path.suffix == ".json":
            import json

            with open(file_path, "r") as f:
                return json.load(f)
        elif file_path.suffix in [".yaml", ".yml"]:
            try:
                import yaml
            except ImportError:
                raise ImportError("PyYAML is required to load YAML files. Install it with 'pip install pyyaml'")

            with open(file_path, "r") as f:
                return yaml.safe_load(f)
        else:
            raise ValueError("Unsupported file format. Use .json or .yaml/.yml.")

    def get(self, path: str, *args: Any, default: Any = None, copy: bool = True) -> Any:
        """
        Get a parameter from the params dictionary using a dot-separated path.
        """
        # Build the navigation path, supporting optional additional path fragments.
        keys = path.split(".")
        if args:
            keys = keys + [str(arg) for arg in args if arg is not None]
        value: dict[str, Any] | list[Any] | tuple[Any, ...] | None = self.params
        for key in keys:
            # Dispatch lookup by container type: mapping keys or sequence indexes.
            if isinstance(value, (dict)) and key in value:
                value = value[key]
            elif isinstance(value, (list, tuple)) and key.isdigit():
                value = value[int(key)]
            else:
                return self.get_parametric_name(default)
        # Return a shallow copy for mutable collections by default to prevent accidental in-place edits.
        if copy and isinstance(value, (dict, list)):
            if isinstance(value, dict):
                value = value.copy()
            else:  # isinstance(value, list)
                value = value.copy()
        if value is None:
            return self.get_parametric_name(default)
        return self.get_parametric_name(value)

    def _normlize_key(self, key: str) -> str:
        """
        Normalize a key by removing leading/trailing whitespace and converting to lowercase.
        """
        return key.replace(".", "_").lower()

    def get_parametric_name(self, name: str | dict[str, Any] | list[Any] | tuple[Any, ...] | set[Any]) -> Any:
        if isinstance(name, str):
            # Start from top-level params so placeholders can reference sibling keys.
            kwargs = self.params.copy()
            keys = [i[1] for i in Formatter().parse(name) if i[1] is not None and i[1] not in kwargs]
            # print(keys)
            if keys:
                for k in keys:
                    if k not in kwargs:
                        # Resolve missing placeholders recursively through the same public API.
                        kwargs[k] = self.get(k)
                    else:
                        kwargs[k] = k
            for k in kwargs:
                name = name.replace("{" + k + "}", str(kwargs[k]))
        elif isinstance(name, dict):
            # Recurse deeply to resolve placeholders in nested containers.
            name = {k: self.get_parametric_name(v) for k, v in name.items()}
        elif isinstance(name, list):
            name = [self.get_parametric_name(n) for n in name]
        elif isinstance(name, tuple):
            name = tuple(self.get_parametric_name(n) for n in name)
        elif isinstance(name, set):  # pyright: ignore[reportUnnecessaryIsInstance]
            name = {
                self.get_parametric_name(n)  # pyright: ignore[reportArgumentType]
                for n in name
                if isinstance(n, Hashable)
            }
        return name

    def get_all(self) -> dict[str, Any]:
        """
        Get the entire params dictionary with all placeholders resolved.
        """
        return self.get_parametric_name(self.params)

    def to_json(self, data: Any = None, indent: int = 2, ensure_ascii: bool = False) -> str:
        """
        Serialize resolved configuration to a JSON string.
        """
        payload = self.get_all() if data is None else data
        return json.dumps(payload, indent=indent, ensure_ascii=ensure_ascii)

    def to_yaml(self, data: Any = None) -> str:
        """
        Serialize resolved configuration to a YAML string.
        """
        try:
            import yaml
        except ImportError as exc:
            raise ImportError("PyYAML is required to dump YAML. Install it with 'pip install pyyaml'") from exc

        payload = self.get_all() if data is None else data
        return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)

    def save(self, file_path: str | Path, data: Any = None, format: str | None = None) -> Path:
        """
        Save configuration (or custom data) to JSON or YAML.

        If format is not provided, it is inferred from the target suffix.
        Supported suffixes: .json, .yaml, .yml.
        Default format is json.
        """
        path = Path(file_path)
        output_format = (format or "").strip().lower()
        if not output_format:
            suffix = path.suffix.lower()
            if suffix in (".yaml", ".yml"):
                output_format = "yaml"
            elif suffix == ".json":
                output_format = "json"
            else:
                output_format = "json"

        if output_format not in {"json", "yaml"}:
            raise ValueError("Unsupported output format. Use 'json' or 'yaml'.")

        payload = self.get_all() if data is None else data
        path.parent.mkdir(parents=True, exist_ok=True)
        if output_format == "json":
            path.write_text(self.to_json(payload), encoding="utf-8")
        else:
            path.write_text(self.to_yaml(payload), encoding="utf-8")
        return path