from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Iterator, Set, cast
from string import Formatter
import json


_MISSING = object()


class DictParser:
    """Dictionary-based configuration parser with placeholder resolution."""

    def __init__(
        self,
        params_or_path: dict[str, Any] | str | Path | DictParser | None,
        folder: str | Path | None = None,
    ) -> None:
        """Create a parser from a mapping, file path, parser, or empty source.

        Args:
            params_or_path: Source dictionary, JSON/YAML path, existing parser,
                or ``None`` for an empty parser.
            folder: Base folder used to resolve relative include/update paths.
        """
        self._params: dict[str, Any] = {}
        self._original_params: dict[str, Any] = {}
        self.cached = False
        if params_or_path is None:
            self.folder = Path.cwd()
            return
        assert isinstance(params_or_path, (dict, str, Path, DictParser)), (
            f"params_or_path must be a dict, a DictParser instance, or a file path (str or Path) and not {type(params_or_path)}"
        )

        if isinstance(params_or_path, dict):
            runtime_folder = Path.cwd()
            self._params = params_or_path
        elif isinstance(params_or_path, DictParser):
            runtime_folder = params_or_path.folder
            self._params = params_or_path.params.copy()
        else:
            path = Path(params_or_path)
            runtime_folder = path.expanduser().resolve().parent
            self._params = self._load_params_from_file(params_or_path)
        self._original_params = self._params.copy()

        self.folder = (Path(folder) if folder is not None else runtime_folder).expanduser().resolve()
        self._invalidate_cache()

    @property
    def params(self) -> dict[str, Any]:
        """Return resolved parameters, rebuilding the cache when required."""
        if not self.cached:
            self._refresh_params()
        return self._params

    @params.setter
    def params(self, value: dict[str, Any]) -> None:
        """Replace source parameters and refresh the resolved cache."""
        self._original_params = value.copy()
        self._invalidate_cache()
        self._refresh_params()

    def merge(
        self,
        params_or_path: dict[str, Any] | str | Path | DictParser | None,
        folder: str | Path | None = None,
    ) -> None:
        """Merge another source into the current source with override precedence.

        Args:
            params_or_path: Source dictionary, file path, parser, or ``None``.
            folder: Optional base folder when ``params_or_path`` is path-based.
        """
        if params_or_path is None:
            return
        other = DictParser(params_or_path, folder=folder)
        self._original_params = self._deep_merge(self._original_params, other._original_params)
        self._invalidate_cache()

    @staticmethod
    def _normalize_path_parts(path: str, *args: Any) -> list[str]:
        # Internal helper: normalize path parts.
        """Internal helper: normalize path parts."""
        keys = path.split(".")
        if args:
            keys = keys + [str(arg) for arg in args if arg is not None]
        return keys

    @staticmethod
    def _ensure_dict(value: Any) -> dict[str, Any]:
        # Internal helper: ensure dict.
        """Internal helper: ensure dict."""
        if isinstance(value, dict):
            return cast(dict[str, Any], value)
        raise ValueError("The provided source must resolve to a dictionary.")

    @staticmethod
    def _clone_value(value: Any) -> Any:
        # Internal helper: clone value.
        """Internal helper: clone value."""
        if isinstance(value, dict):
            value_dict = cast(dict[str, Any], value)
            return {k: DictParser._clone_value(v) for k, v in value_dict.items()}
        if isinstance(value, list):
            value_list = cast(list[Any], value)
            return [DictParser._clone_value(v) for v in value_list]
        if isinstance(value, tuple):
            value_tuple = cast(tuple[Any, ...], value)
            return tuple(DictParser._clone_value(v) for v in value_tuple)
        if isinstance(value, set):
            value_set = cast(set[Any], value)
            return {DictParser._clone_value(v) for v in value_set}
        return value

    @staticmethod
    def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        # Internal helper: deep merge.
        """Internal helper: deep merge."""
        merged = {k: DictParser._clone_value(v) for k, v in base.items()}
        for key, value in override.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged_base = cast(dict[str, Any], merged[key])
                merged_override = cast(dict[str, Any], value)
                merged[key] = DictParser._deep_merge(merged_base, merged_override)
            else:
                merged[key] = DictParser._clone_value(value)
        return merged

    def _iter_sources(
        self,
        source_or_sources: str | Path | dict[str, Any] | list[str | Path | dict[str, Any]],
    ) -> Iterable[str | Path | dict[str, Any]]:
        # Internal helper: iter sources.
        """Internal helper: iter sources."""
        if isinstance(source_or_sources, list):
            return source_or_sources
        return [source_or_sources]

    def _resolve_file_path(self, file_path: str | Path) -> Path:
        # Internal helper: resolve file path.
        """Internal helper: resolve file path."""
        path = Path(file_path)
        if not path.is_absolute():
            path = self.folder / path
        return path.expanduser().resolve()

    def _load_source_dict(self, source: str | Path | dict[str, Any]) -> dict[str, Any]:
        # Internal helper: load source dict.
        """Internal helper: load source dict."""
        if isinstance(source, dict):
            return source
        resolved = self._resolve_file_path(source)
        return self._load_params_from_file(resolved)

    def _invalidate_cache(self) -> None:
        # Internal helper: invalidate cache.
        """Internal helper: invalidate cache."""
        self._params = {}
        self.cached = False

    def _refresh_params(self) -> None:
        # Internal helper: refresh params.
        """Internal helper: refresh params."""
        self._params = self.get_all()
        self.cached = True

    def _load_params_from_file(self, file_path: str | Path) -> dict[str, Any]:
        # Internal helper: load params from file.
        """Internal helper: load params from file."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if file_path.suffix == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                return self._ensure_dict(loaded)
        elif file_path.suffix in [".yaml", ".yml"]:
            try:
                import yaml
            except ImportError:
                raise ImportError("PyYAML is required to load YAML files. Install it with 'pip install pyyaml'")

            with open(file_path, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
                return self._ensure_dict(loaded)
        else:
            raise ValueError("Unsupported file format. Use .json or .yaml/.yml.")

    def get(self, path: str, *args: Any, default: Any = None, copy: bool = True, use_cache: bool = True) -> Any:
        """Get a value by dot-path with optional wildcard list expansion.

        Args:
            path: Dot-separated key path.
            *args: Optional additional path segments appended to ``path``.
            default: Fallback value when the path does not exist.
            copy: When ``True``, shallow-copy ``dict`` and ``list`` results.
            use_cache: When ``True``, read from resolved cached parameters.

        Returns:
            Resolved value, wildcard-expanded list, or ``default`` when missing.
        """
        # Build the navigation path, supporting optional additional path fragments.
        keys = self._normalize_path_parts(path, *args)
        value: dict[str, Any] | list[Any] | tuple[Any, ...] | None = self.params if use_cache else self._original_params
        parsed: bool = False
        for i in range(len(keys)):
            key: str = keys[i]
            # Dispatch lookup by container type: mapping keys or sequence indexes.
            if isinstance(value, (dict)) and key in value:
                value = value[key]
            elif isinstance(value, (list, tuple)) and key.isdigit():
                value = value[int(key)]
            elif isinstance(value, (list, tuple)) and key == "*":
                if i < len(keys) - 1:
                    value = [
                        self.get(
                            ".".join(keys[:i] + [str(idx)] + keys[i + 1 :]),
                            default=default,
                            use_cache=use_cache,
                        )
                        for idx, _ in enumerate(value)
                    ]
                else:
                    value = [
                        self.get(".".join(keys[:i] + [str(idx)]), default=default, use_cache=use_cache)
                        for idx, _ in enumerate(value)
                    ]
                parsed = True
                break
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
        if parsed:
            return value
        else:
            return self.get_parametric_name(value)

    def _path_exists(self, path: str) -> bool:
        # Internal helper: path exists.
        """Internal helper: path exists."""
        keys = self._normalize_path_parts(path)
        value: Any = self.params
        for key in keys:
            if isinstance(value, dict) and key in value:
                value_dict = cast(dict[str, Any], value)
                value = value_dict[key]
            elif isinstance(value, list) and key.isdigit():
                value_list = cast(list[Any], value)
                idx = int(key)
                if idx >= len(value_list):
                    return False
                value = value_list[idx]
            else:
                return False
        return True

    def _iter_deep_items(self, value: Any, prefix: str = "") -> Iterator[tuple[str, Any]]:
        # Internal helper: iter deep items.
        """Internal helper: iter deep items."""
        if isinstance(value, dict):
            value_dict = cast(dict[str, Any], value)
            for key, item in value_dict.items():
                item_path = f"{prefix}.{key}" if prefix else key
                yield item_path, item
                yield from self._iter_deep_items(item, item_path)
        elif isinstance(value, list):
            value_list = cast(list[Any], value)
            for idx, item in enumerate(value_list):
                item_path = f"{prefix}.{idx}" if prefix else str(idx)
                yield item_path, item
                yield from self._iter_deep_items(item, item_path)

    def set(self, path: str, value: Any) -> None:
        """Set or create a value at a dot-path.

        Args:
            path: Dot-separated target path.
            value: Value assigned at the target path.
        """
        keys = self._normalize_path_parts(path)
        if not keys:
            raise ValueError("Path cannot be empty")

        current: Any = self._original_params
        for index, key in enumerate(keys[:-1]):
            next_key = keys[index + 1]
            next_is_index = next_key.isdigit()

            if isinstance(current, dict):
                current_dict = cast(dict[str, Any], current)
                if key not in current_dict or not isinstance(current_dict[key], (dict, list)):
                    current_dict[key] = [] if next_is_index else {}
                current = current_dict[key]
            elif isinstance(current, list):
                current_list = cast(list[Any], current)
                if not key.isdigit():
                    raise KeyError(f"Expected numeric index at segment '{key}'")
                idx = int(key)
                while len(current_list) <= idx:
                    current_list.append(None)
                if current_list[idx] is None or not isinstance(current_list[idx], (dict, list)):
                    current_list[idx] = [] if next_is_index else {}
                current = current_list[idx]
            else:
                raise KeyError(f"Cannot navigate through non-container value at segment '{key}'")

        last = keys[-1]
        if isinstance(current, dict):
            current_dict = cast(dict[str, Any], current)
            current_dict[last] = value
        elif isinstance(current, list):
            current_list = cast(list[Any], current)
            if not last.isdigit():
                raise KeyError(f"Expected numeric index at segment '{last}'")
            idx = int(last)
            while len(current_list) <= idx:
                current_list.append(None)
            current_list[idx] = value
        else:
            raise KeyError("Cannot assign to non-container target")

        self._invalidate_cache()

    def setdefault(self, path: str, default: Any = None) -> Any:
        """Get a path value, creating it with ``default`` when missing.

        Args:
            path: Dot-separated target path.
            default: Value used when ``path`` is missing.

        Returns:
            Existing or newly assigned value at ``path``.
        """
        if self._path_exists(path):
            return self.get(path)
        self.set(path, default)
        return self.get(path)

    def delete(self, path: str) -> None:
        """Delete a value at a dot-path.

        Args:
            path: Dot-separated target path.
        """
        keys = self._normalize_path_parts(path)
        if not keys:
            raise KeyError("Path cannot be empty")

        current: Any = self._original_params
        for key in keys[:-1]:
            if isinstance(current, dict) and key in current:
                current_dict = cast(dict[str, Any], current)
                current = current_dict[key]
            elif isinstance(current, list) and key.isdigit():
                current_list = cast(list[Any], current)
                idx = int(key)
                if idx >= len(current_list):
                    raise KeyError(path)
                current = current_list[idx]
            else:
                raise KeyError(path)

        last = keys[-1]
        if isinstance(current, dict) and last in current:
            current_dict = cast(dict[str, Any], current)
            del current_dict[last]
        elif isinstance(current, list) and last.isdigit():
            current_list = cast(list[Any], current)
            idx = int(last)
            if idx >= len(current_list):
                raise KeyError(path)
            del current_list[idx]
        else:
            raise KeyError(path)

        self._invalidate_cache()

    def include(self, source_or_sources: str | Path | dict[str, Any] | list[str | Path | dict[str, Any]]) -> None:
        """Include a source without overriding existing values.

        Args:
            source_or_sources: One or more dictionaries or JSON/YAML paths.
        """
        included: dict[str, Any] = {}
        for source in self._iter_sources(source_or_sources):
            loaded = self._ensure_dict(self._load_source_dict(source))
            included = self._deep_merge(included, loaded)
        self._original_params = self._deep_merge(included, self._original_params)
        self._invalidate_cache()

    def update(self, source_or_sources: str | Path | dict[str, Any] | list[str | Path | dict[str, Any]]) -> None:
        """Update current parameters with one or more overriding sources.

        Args:
            source_or_sources: One or more dictionaries or JSON/YAML paths.
        """
        updated: dict[str, Any] = {}
        for source in self._iter_sources(source_or_sources):
            loaded = self._ensure_dict(self._load_source_dict(source))
            updated = self._deep_merge(loaded, updated)
        self._original_params = self._deep_merge(self._original_params, updated)
        self._invalidate_cache()

    def contains(self, key: str, deep: bool = False) -> bool:
        """Check whether a key path exists.

        Args:
            key: Dot path or key name.
            deep: When ``True``, also match nested key names.

        Returns:
            ``True`` when the key is found.
        """
        if self._path_exists(key):
            return True
        if not deep:
            return False
        key_str = str(key)
        for item_path, _ in self._iter_deep_items(self.params):
            if item_path == key_str or item_path.split(".")[-1] == key_str:
                return True
        return False

    def has_key(self, key: str, deep: bool = False) -> bool:
        """Alias of :meth:`contains`.

        Args:
            key: Dot path or key name.
            deep: When ``True``, also match nested key names.

        Returns:
            ``True`` when the key is found.
        """
        return self.contains(key, deep=deep)

    def items(self, deep: bool = False) -> list[tuple[str, Any]]:
        """Return key-value pairs.

        Args:
            deep: When ``True``, include nested dot-path entries.

        Returns:
            List of key-value pairs.
        """
        if not deep:
            return list(self.params.items())
        return list(self._iter_deep_items(self.params))

    def keys(self, deep: bool = False) -> list[str]:
        """Return keys.

        Args:
            deep: When ``True``, include nested dot-path keys.

        Returns:
            List of keys.
        """
        return [key for key, _ in self.items(deep=deep)]

    def values(self, deep: bool = False) -> list[Any]:
        """Return values.

        Args:
            deep: When ``True``, include values from nested entries.

        Returns:
            List of values.
        """
        return [value for _, value in self.items(deep=deep)]

    def pop(self, path: str, default: Any = _MISSING) -> Any:
        """Remove and return a value from a dot-path.

        Args:
            path: Dot-separated target path.
            default: Returned when ``path`` is missing.

        Returns:
            Removed value, or ``default`` when provided and missing.
        """
        if not self._path_exists(path):
            if default is _MISSING:
                raise KeyError(path)
            return default
        value = self.get(path)
        self.delete(path)
        return value

    def popitem(self, deep: bool = False) -> tuple[str, Any]:
        """Remove and return one key-value pair.

        Args:
            deep: When ``True``, remove the last nested item by deep traversal.

        Returns:
            Removed key and value.
        """
        if deep:
            deep_items = self.items(deep=True)
            if not deep_items:
                raise KeyError("popitem(): dictionary is empty")
            key, _ = deep_items[-1]
            value = self.get(key)
            self.delete(key)
            return key, value

        if not self.params:
            raise KeyError("popitem(): dictionary is empty")
        key, value = self.params.popitem()
        self._original_params.pop(key)
        self._invalidate_cache()
        return key, value

    def clear(self) -> None:
        """Remove all source parameters and invalidate the resolved cache."""
        self._original_params.clear()
        self._invalidate_cache()

    def copy(self, parsed: bool = False) -> dict[str, Any]:
        """Return a shallow copy of source or resolved parameters.

        Args:
            parsed: When ``True``, return resolved parameters.

        Returns:
            Copied parameter dictionary.
        """
        return self._original_params.copy() if not parsed else self.params.copy()

    def __getitem__(self, key: str) -> Any:
        """Return a value by dot-path.

        Args:
            key: Dot-separated target path.

        Returns:
            Value associated with ``key``.
        """
        if not self._path_exists(key):
            raise KeyError(key)
        return self.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Assign a value using dot-path semantics.

        Args:
            key: Dot-separated target path.
            value: Value assigned at ``key``.
        """
        self.set(key, value)

    def __delitem__(self, key: str) -> None:
        """Delete a value by dot-path.

        Args:
            key: Dot-separated target path.
        """
        self.delete(key)

    def __contains__(self, key: object) -> bool:
        """Return whether a top-level path exists.

        Args:
            key: Candidate key object.

        Returns:
            ``True`` only for existing string keys.
        """
        if not isinstance(key, str):
            return False
        return self.contains(key, deep=False)

    def __iter__(self) -> Iterator[str]:
        """Iterate over top-level keys.

        Returns:
            Iterator over top-level key names.
        """
        return iter(self.params)

    def __len__(self) -> int:
        """Return number of top-level keys.

        Returns:
            Number of top-level items.
        """
        return len(self.params)

    def _normlize_key(self, key: str) -> str:
        """
        Normalize a key by removing leading/trailing whitespace and converting to lowercase.
        """
        # Internal helper: normlize key.
        return key.replace(".", "_").lower()

    def get_parametric_name(self, name: str | dict[str, Any] | list[Any] | tuple[Any, ...] | Set[Any]) -> Any:
        """Resolve placeholders recursively in strings and nested containers.

        Args:
            name: Value or container potentially containing ``{path}`` placeholders.

        Returns:
            Value with placeholders resolved.
        """
        if isinstance(name, str):
            # Start from top-level params so placeholders can reference sibling keys.
            kwargs = self._original_params.copy()
            keys = [i[1] for i in Formatter().parse(name) if i[1] is not None and i[1] not in kwargs]
            # print(keys)
            if keys:
                for k in keys:
                    if k not in kwargs:
                        # Resolve missing placeholders recursively through the same public API.
                        kwargs[k] = self.get(k, use_cache=False)
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
            results = (self.get_parametric_name(n) for n in name)
            name = {n for n in results if isinstance(n, (str, int, float, bool, tuple))}
        return name

    def get_all(self) -> dict[str, Any]:
        """
        Get the entire params dictionary with all placeholders resolved.
        """
        return self.get_parametric_name(self._original_params)

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
