# Internationalization (i18n) Guide

This document explains how the multi-language support system works in checkpatch.

## Overview

The checkpatch system now supports multiple languages through a JSON-based internationalization (i18n) system. All user-facing text (console output, HTML reports, JSON messages) can be displayed in different languages.

## Supported Languages

Currently supported languages:
- **Spanish (es)** - Default language
- **English (en)**

## Usage

### Command Line

Use the `--language` flag to set the interface language:

```bash
# Spanish (default)
./main.py --analyze /path/to/kernel --language es

# English
./main.py --analyze /path/to/kernel --language en
```

### In Code

The i18n system is implemented in the `i18n.py` module:

```python
# Import the i18n module
from i18n import get_text as _

# Set the language
import i18n
i18n.set_language('en')

# Get translated text
title = _('html.dashboard_title')
error_msg = _('errors.file_not_exist', file='/path/to/file')
```

## File Structure

### Language Files

Language files are stored in the `i18n/` directory as JSON files:

```
i18n/
├── es.json  # Spanish translations
└── en.json  # English translations
```

### JSON Structure

Each language file contains a hierarchical structure of translations:

```json
{
  "analyzer": {
    "analyzing": "Analyzing {total} files with {workers} workers...",
    "errors_found": "Errors found: {count}"
  },
  "html": {
    "dashboard_title": "Checkpatch Dashboard",
    "global_summary": "Global Summary"
  },
  "errors": {
    "file_not_exist": "File does not exist: {file}"
  }
}
```

### String Keys

Strings are organized by category:
- `analyzer.*` - Analysis mode messages
- `autofix.*` - Autofix mode messages
- `compile.*` - Compilation mode messages
- `errors.*` - Error messages
- `html.*` - HTML report strings
- `cli.*` - Command-line interface strings
- `main.*` - Main module strings

### Placeholders

Strings can contain placeholders using Python's format string syntax:

```json
{
  "analyzer.analyzing": "Analyzing {total} files with {workers} workers..."
}
```

Usage in code:

```python
_('analyzer.analyzing', total=100, workers=4)
# Output: "Analyzing 100 files with 4 workers..."
```

## Adding a New Language

To add a new language (e.g., French):

1. Create a new JSON file in `i18n/` directory:
   ```bash
   cp i18n/en.json i18n/fr.json
   ```

2. Translate all strings in the new file:
   ```json
   {
     "analyzer": {
       "analyzing": "Analyse de {total} fichiers avec {workers} workers...",
       ...
     }
   }
   ```

3. Update the `--language` argument in `main.py`:
   ```python
   logging_group.add_argument("--language", 
                             choices=["es", "en", "fr"],  # Add "fr"
                             default="es",
                             help="Interface language (default: es)")
   ```

4. Test the new language:
   ```bash
   ./main.py --analyze /path/to/kernel --language fr
   ```

## Adding New Strings

When adding new user-facing text to the code:

1. Add the string to both `i18n/es.json` and `i18n/en.json`:

   **es.json:**
   ```json
   {
     "analyzer": {
       "new_message": "Nuevo mensaje: {value}"
     }
   }
   ```

   **en.json:**
   ```json
   {
     "analyzer": {
       "new_message": "New message: {value}"
     }
   }
   ```

2. Use the string in code:
   ```python
   from i18n import get_text as _
   
   message = _('analyzer.new_message', value=42)
   logger.info(message)
   ```

## Best Practices

### String Keys

- Use descriptive, hierarchical keys: `category.specific_message`
- Group related strings together
- Use consistent naming conventions

### Placeholders

- Use descriptive placeholder names: `{count}`, `{file}`, `{path}`
- Keep placeholders consistent across languages
- Document expected placeholder types (string, int, float)

### Testing

Always test with multiple languages to ensure:
- All strings are translated
- Placeholder formatting works correctly
- No missing keys
- HTML reports render correctly

## Implementation Details

### The i18n Module

The `i18n.py` module provides:

- **LocaleManager**: Singleton class managing language state
- **set_language(code)**: Sets the active language
- **get_text(key, **kwargs)**: Gets translated text with formatting
- **get_language()**: Returns current language code
- **get_available_languages()**: Lists available languages

### Fallback Behavior

If a string key is not found:
- Returns `[MISSING: key]` to indicate the missing translation
- Logs a warning (optional)

If a language file doesn't exist:
- Falls back to Spanish (es)
- Logs a warning

### Performance

- Language files are loaded once on first use
- Strings are cached in memory
- No runtime overhead for string lookups

## Current Coverage

### Fully Internationalized

- ✅ Console output (main.py)
- ✅ Error messages (main.py, compile.py)
- ✅ HTML report titles and headers (report.py)
- ✅ CLI help text (main.py)

### Partially Internationalized

- ⚠️ HTML report content (report.py) - some strings remain
- ⚠️ JSON output - currently uses same language as interface

### Not Yet Internationalized

- ❌ Documentation files (README.md, etc.)
- ❌ Code comments and docstrings
- ❌ Test output

## Future Enhancements

Potential improvements:
- Add more languages (French, German, Portuguese, etc.)
- Translate documentation files
- Add language detection based on system locale
- Support for plural forms
- Support for date/time formatting per locale
- Translation validation script
- Automated translation using translation APIs

## Troubleshooting

### String Not Appearing Translated

1. Check that the key exists in the language file
2. Verify the language is set correctly
3. Check for typos in the key name
4. Ensure placeholders match

### Missing Placeholder Error

If you see `[FORMAT_ERROR: key - missing param X]`:
- Check that all required placeholders are provided
- Verify placeholder names match between code and JSON

### Language File Not Loading

- Check file exists in `i18n/` directory
- Verify JSON syntax is valid
- Check file permissions

## Contributing

When contributing new features:
1. Add all new strings to both es.json and en.json
2. Use the `_()` function for all user-facing text
3. Test with both languages
4. Update this documentation if adding new categories

For questions or suggestions, please open an issue on GitHub.
