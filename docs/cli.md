# CLI

The package declares a `dictparser` console script through:

- `project.scripts.dictparser = dictparser.__main__:main`

If your project provides a CLI entry point module, invoke it as:

```bash
dictparser --help
```

If no CLI module is available yet, use the library API directly (see [library.md](library.md)).
