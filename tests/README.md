# Tests

BookScreenshot uses [pytest](https://docs.pytest.org/) for automated testing.

## Running tests

From the project root, run:

```bash
python -m pytest
```

To display more detailed output:

```bash
python -m pytest -v
```

## Testing principles

- Tests should be independent and repeatable.
- Tests should not require real screenshots, user files, or external services.
- Windows-specific functionality should be tested separately where necessary.
- Temporary files should use pytest's temporary-directory fixtures.
- Optional modules should not be required to run core tests.

## Planned test areas

- Configuration and profile management
- Screenshot capture and image handling
- Batch processing
- Session saving and recovery
- PDF generation
- Keyboard shortcuts
- Optional module integration
