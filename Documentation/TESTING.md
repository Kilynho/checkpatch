# Testing Guide for Checkpatch Autofix

This document explains how to write and run tests for checkpatch autofix functions.

## Overview

The project has comprehensive unit tests for all fix functions in `test_fixes.py`. Tests run automatically on every push via GitHub Actions.

## Running Tests

### Run all tests:
```bash
python3 test_fixes.py
```

### Run tests with verbose output:
```bash
python3 test_fixes.py -v
```

### Run a specific test:
```bash
python3 -m unittest test_fixes.TestFixFunctions.test_fix_indent_tabs
```

## Test Structure

Tests are organized in `test_fixes.py`:

- **TestFixFunctions**: Unit tests for individual fix functions (30+ tests)
- **TestFixFunctionsIntegration**: Integration tests for complex scenarios

Each test:
1. Creates a temporary file with problematic code
2. Applies the fix function
3. Verifies the result is correct

## Adding Tests for New Fixes

### Step 1: Implement your fix in `core.py`

```python
def fix_new_rule(file_path, line_number):
    """Fix description."""
    def callback(lines, idx):
        # Your fix logic here
        line = lines[idx]
        if "pattern" in line:
            lines[idx] = line.replace("pattern", "replacement")
            return True
        return False
    return apply_lines_callback(file_path, line_number, callback)
```

### Step 2: Register in `engine.py`

```python
AUTO_FIX_RULES = {
    # ... existing rules ...
    "Your error message from checkpatch": fix_new_rule,
}
```

### Step 3: Add test in `test_fixes.py`

Add a new test method to the `TestFixFunctions` class:

```python
def test_fix_new_rule(self):
    """Test fix_new_rule does what it should."""
    # 1. Create test file with problematic code
    content = "old pattern here\n"
    test_file = self.create_test_file(content)
    
    # 2. Apply the fix
    result = fix_new_rule(test_file, 1)
    self.assertTrue(result, "Fix should be applied")
    
    # 3. Verify the result
    fixed_content = self.read_file(test_file)
    self.assertIn("replacement", fixed_content)
    self.assertNotIn("old pattern", fixed_content)
```

### Step 4: Import your fix function

Add your fix to the imports at the top of `test_fixes.py`:

```python
from core import (
    # ... existing imports ...
    fix_new_rule,
)
```

### Step 5: Run tests

```bash
python3 test_fixes.py
```

Verify your test passes!

## Test Best Practices

### 1. Test the positive case (fix should apply)
```python
def test_fix_something(self):
    """Test fix applies to correct pattern."""
    content = "bad pattern\n"
    test_file = self.create_test_file(content)
    
    result = fix_something(test_file, 1)
    self.assertTrue(result, "Fix should apply")
    
    fixed_content = self.read_file(test_file)
    self.assertIn("good pattern", fixed_content)
```

### 2. Test edge cases
```python
def test_fix_something_edge_case(self):
    """Test fix handles edge case correctly."""
    content = "edge case pattern\n"
    test_file = self.create_test_file(content)
    
    result = fix_something(test_file, 1)
    # May return True or False depending on your fix
    self.assertIsInstance(result, bool)
```

### 3. Test multi-line fixes
```python
def test_fix_multiline(self):
    """Test fix handles multiple lines."""
    content = "line 1\nline 2\nline 3\n"
    test_file = self.create_test_file(content)
    
    result = fix_something(test_file, 2)
    
    fixed_content = self.read_file(test_file)
    lines = fixed_content.split('\n')
    self.assertEqual(len(lines), 4)  # 3 lines + empty at end
```

### 4. Use descriptive assertions
```python
# Good
self.assertTrue(result, "Should convert strcpy to strscpy")
self.assertIn("strscpy", fixed_content, "Fixed code should use strscpy")

# Less helpful
self.assertTrue(result)
self.assertIn("strscpy", fixed_content)
```

### 5. Keep tests independent
Each test should:
- Create its own test file
- Not depend on other tests
- Clean up after itself (handled by tearDown)

## Common Test Patterns

### Testing pattern replacement:
```python
def test_fix_pattern_replacement(self):
    content = "old_function();\n"
    test_file = self.create_test_file(content)
    
    result = fix_pattern_replacement(test_file, 1)
    self.assertTrue(result)
    
    fixed_content = self.read_file(test_file)
    self.assertIn("new_function()", fixed_content)
    self.assertNotIn("old_function()", fixed_content)
```

### Testing line deletion:
```python
def test_fix_removes_line(self):
    content = "keep this\nremove this\nkeep this\n"
    test_file = self.create_test_file(content)
    
    result = fix_removes_line(test_file, 2)
    self.assertTrue(result)
    
    fixed_content = self.read_file(test_file)
    lines = fixed_content.split('\n')
    self.assertEqual(len(lines), 3)  # 2 lines + empty
    self.assertNotIn("remove this", fixed_content)
```

### Testing line insertion:
```python
def test_fix_inserts_line(self):
    content = "line 1\nline 2\n"
    test_file = self.create_test_file(content)
    
    result = fix_inserts_line(test_file, 2)
    self.assertTrue(result)
    
    fixed_content = self.read_file(test_file)
    lines = fixed_content.split('\n')
    self.assertEqual(len(lines), 4)  # 3 lines + empty
```

## Integration Tests

For complex scenarios testing multiple fixes:

```python
class TestFixFunctionsIntegration(unittest.TestCase):
    def test_complex_scenario(self):
        """Test multiple fixes work together."""
        content = '''printk(KERN_INFO "test");
        int x = 5;   
'''
        test_file = self.create_test_file(content)
        
        # Apply multiple fixes
        fix_printk_info(test_file, 1)
        fix_indent_tabs(test_file, 2)
        fix_trailing_whitespace(test_file, 2)
        
        fixed_content = self.read_file(test_file)
        self.assertIn("pr_info", fixed_content)
        self.assertIn("\t", fixed_content)
```

## Continuous Integration

Tests run automatically via GitHub Actions on:
- Every push to main/master/develop branches
- Every pull request
- Manual workflow dispatch

See `.github/workflows/test.yml` for configuration.

## Test Coverage

Current test coverage:

- ✅ 30+ individual fix function tests
- ✅ 2 integration tests
- ✅ All active fixes in `engine.py` are covered

## Troubleshooting

### Test fails locally but passes in CI:
- Check Python version (we use 3.12)
- Check line ending differences (Unix vs Windows)
- Run with `-v` flag for detailed output

### Test passes but fix doesn't work in practice:
- Your test pattern may be too simple
- Add more realistic test cases
- Test with actual checkpatch warning messages

### Fix modifies file but test fails:
- Check if fix returns True/False correctly
- Verify file content with `print(fixed_content)`
- Check for whitespace/newline differences

## Additional Resources

- See existing tests in `test_fixes.py` for examples
- Read `ARCHITECTURE.md` for overall system design
- Check `FIXES_STATUS.md` for fix implementation status
- Review `core.py` for fix function patterns

## Quick Checklist

When adding a new fix:

- [ ] Implement fix function in `core.py`
- [ ] Register in `AUTO_FIX_RULES` in `engine.py`
- [ ] Import in `test_fixes.py`
- [ ] Add test method to `TestFixFunctions`
- [ ] Run `python3 test_fixes.py` and verify it passes
- [ ] Commit and push - CI will run automatically
- [ ] Update `FIXES_STATUS.md` with new fix status

---

**Questions?** Open an issue or check existing tests for examples.
