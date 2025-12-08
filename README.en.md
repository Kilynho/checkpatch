# Checkpatch - Analyzer & Autofix System

**All documentation can be found in the `documentation/` folder** → [📚 View documentation](documentation/README.md)

Unified system for analysis and automatic correction of **checkpatch.pl** (Linux kernel) warnings/errors.

## 🚀 Quick Start

### Installation

```bash
# Clone or download the repository
cd checkpatch

# Grant execution permissions
chmod +x main.py run
```

### Basic Usage

```bash
# 1. Analyze files with checkpatch
./main.py --analyze /path/to/kernel/linux --paths init --language en

# 2. View report (open in browser)
open html/dashboard.html

# 3. Apply automatic fixes
./main.py --fix --json-input json/checkpatch.json --language en

# 4. Compile modified files (verify they compile)
./main.py --compile --json-input json/fixed.json --kernel-root /path/to/kernel/linux --restore-after

# 5. View results
open html/dashboard.html  # Automatically updated
```

Or run everything automatically:
```bash
./run
```

---

## 🌍 Multi-Language Support

The system supports multiple languages for the interface:

```bash
# Spanish (default)
./main.py --analyze /path/to/kernel --language es

# English
./main.py --analyze /path/to/kernel --language en
```

See [INTERNATIONALIZATION.md](documentation/INTERNATIONALIZATION.md) for more details.

---

## 📋 Project Structure

```
checkpatch/
├── main.py              # Entry point (--analyze, --fix, --compile)
├── engine.py            # Analysis and fixes logic
├── core.py              # Fix implementations (40+)
├── compile.py           # File compilation module
├── report.py            # HTML generators (8 reports)
├── logger.py            # Unified logging system ⭐ NEW
├── i18n.py              # Internationalization system ⭐ NEW
├── utils.py             # Common utilities
├── constants.py         # Constants and patterns
├── run                  # Automated script
│
├── README.md            # This file
├── README.en.md         # English version
├── TESTING.md           # Testing guide
│
├── i18n/                # Language files ⭐ NEW
│   ├── es.json                 # Spanish translations
│   └── en.json                 # English translations
│
├── documentation/       # Complete documentation
│   ├── README.md                # Documentation index ⭐
│   ├── ARCHITECTURE.md          # Detailed architecture
│   ├── CHANGELOG.md             # Change history
│   ├── HTML_REPORTS.md          # Report structure
│   ├── QUICK_REFERENCE.md       # Quick guide
│   ├── INTERNATIONALIZATION.md  # i18n guide ⭐ NEW
│   └── ...
│
├── html/                # Generated reports
│   ├── dashboard.html           # Main hub
│   ├── analyzer.html            # Analysis summary
│   └── ...
│
└── json/                # Processed data
    ├── checkpatch.json  # Found issues
    ├── fixed.json       # Fixed issues
    └── compile.json     # Compilation results
```

---

## 📊 HTML Reports

Modular system of **8 interconnected reports** with breadcrumb navigation:

1. **dashboard.html** - Main hub with tabs
2. **analyzer.html** - Analysis summary
3. **detail-reason.html** - Detail by issue type
4. **detail-file.html** - Detail by file
5. **autofix.html** - Autofix summary
6. **autofix-detail-reason.html** - Autofix by type
7. **autofix-detail-file.html** - Autofix by file
8. **compile.html** - Compilation report

---

## 🛠️ Main Commands

### Analysis Mode

```bash
# Analyze specific subdirectories
./main.py --analyze /path/to/kernel --paths init kernel --language en

# Analyze entire kernel
./main.py --analyze /path/to/kernel --language en

# Custom output
./main.py --analyze /path/to/kernel \
  --paths init \
  --html custom/report.html \
  --json-out custom/data.json \
  --language en
```

### Autofix Mode

```bash
# Fix all issues
./main.py --fix --json-input json/checkpatch.json --language en

# Fix only errors
./main.py --fix --json-input json/checkpatch.json --type error

# Fix specific file
./main.py --fix --json-input json/checkpatch.json --file /path/to/file.c
```

### Compilation Mode

```bash
# Compile and restore
./main.py --compile \
  --json-input json/fixed.json \
  --kernel-root /path/to/kernel \
  --restore-after \
  --language en

# Compile without cleanup
./main.py --compile \
  --json-input json/fixed.json \
  --kernel-root /path/to/kernel \
  --no-cleanup
```

---

## 🔍 Logging System

Unified logging with configurable levels:

```bash
# Debug level
./main.py --analyze /path/to/kernel --log-level DEBUG --language en

# Save to file
./main.py --analyze /path/to/kernel --log-file logs/analysis.log

# Without colors
./main.py --analyze /path/to/kernel --no-color
```

Logging levels: DEBUG, INFO (default), WARNING, ERROR, CRITICAL

---

## 🧪 Testing

```bash
# Run unit tests
python3 test_fixes.py

# Verbose output
python3 test_fixes.py -v
```

See [TESTING.md](TESTING.md) for the complete testing guide.

---

## 📚 Complete Documentation

- **[Documentation Index](documentation/README.md)** - Complete guide
- **[Architecture](documentation/ARCHITECTURE.md)** - System design
- **[HTML Reports](documentation/HTML_REPORTS.md)** - Report structure
- **[Quick Reference](documentation/QUICK_REFERENCE.md)** - Quick commands
- **[Internationalization](documentation/INTERNATIONALIZATION.md)** - Multi-language guide ⭐
- **[Testing Guide](documentation/TESTING.md)** - Testing instructions
- **[Changelog](documentation/CHANGELOG.md)** - Version history

---

## ✨ Key Features

- ✅ **40+ automatic fixes** for common checkpatch warnings
- ✅ **8 interconnected HTML reports** with breadcrumb navigation
- ✅ **Compilation verification** for modified files
- ✅ **Unified logging system** with configurable levels
- ✅ **Multi-language support** (Spanish, English) ⭐ NEW
- ✅ **100% test coverage** for all fixes
- ✅ **Parallel processing** with configurable workers
- ✅ **JSON output** for automation
- ✅ **Backup and restore** system

---

## 🤝 Contributing

Contributions are welcome! When adding new features:
1. Add all user-facing text to both `i18n/es.json` and `i18n/en.json`
2. Follow existing code style
3. Add unit tests
4. Update documentation
5. Test with both languages

---

## 📝 License

This project is part of the Linux kernel development tools ecosystem.

---

## 🔗 Related Documentation

- [Architecture Details](documentation/ARCHITECTURE.md)
- [HTML Reports Guide](documentation/HTML_REPORTS.md)
- [Testing Guide](documentation/TESTING.md)
- [Internationalization Guide](documentation/INTERNATIONALIZATION.md) ⭐

---

**Note**: For Spanish documentation, see [README.md](README.md)
