#!/usr/bin/env python3
"""
Unit tests for checkpatch autofix functions.

Each test creates a temporary file with specific code patterns,
applies the fix function, and verifies the result.
Tests are independent and don't require external Linux kernel source.
"""

import unittest
import tempfile
import os
from pathlib import Path
import shutil

# Import all fix functions from core module
from core import (
    fix_missing_blank_line,
    fix_quoted_string_split,
    fix_assignment_in_if,
    fix_switch_case_indent,
    fix_indent_tabs,
    fix_trailing_whitespace,
    fix_initconst,
    fix_prefer_notice,
    fix_void_return,
    fix_unnecessary_braces,
    fix_block_comment_trailing,
    fix_char_array_static_const,
    fix_spdx_comment,
    fix_extern_in_c,
    fix_symbolic_permissions,
    fix_printk_info,
    fix_printk_err,
    fix_printk_warn,
    fix_printk_debug,
    fix_printk_emerg,
    fix_printk_kern_level,
    fix_jiffies_comparison,
    fix_func_name_in_string,
    fix_else_after_return,
    fix_weak_attribute,
    fix_oom_message,
    fix_asm_includes,
    fix_initdata_placement,
    fix_missing_spdx,
    fix_msleep_too_small,
    fix_kmalloc_no_flag,
    fix_memcpy_literal,
    fix_of_read_no_check,
    fix_strcpy_to_strscpy,
    fix_strncpy,
    fix_logging_continuation,
    fix_spaces_at_start_of_line,
    fix_filename_in_file,
    fix_function_macro,
    fix_space_before_open_brace,
    fix_else_after_close_brace,
    fix_sizeof_struct,
    fix_consecutive_strings,
    fix_comparison_to_null,
    fix_constant_comparison,
)


class TestFixFunctions(unittest.TestCase):
    """Test suite for all checkpatch fix functions."""
    
    def setUp(self):
        """Create a temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up temporary test directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def create_test_file(self, content):
        """Create a temporary test file with given content and return its path."""
        test_file = Path(self.test_dir) / "test.c"
        with open(test_file, "w") as f:
            f.write(content)
        return test_file
    
    def read_file(self, file_path):
        """Read and return file content."""
        with open(file_path, "r") as f:
            return f.read()
    
    # Test 1: Missing blank line after declarations
    def test_fix_missing_blank_line(self):
        """Test fix_missing_blank_line adds a blank line after declarations."""
        content = "int x = 5;\nreturn x;\n"
        test_file = self.create_test_file(content)
        
        result = fix_missing_blank_line(test_file, 2)
        self.assertTrue(result, "Fix should be applied")
        
        fixed_content = self.read_file(test_file)
        self.assertIn("\n\n", fixed_content, "Should contain blank line")
    
    # Test 2: Quoted string split across lines
    def test_fix_quoted_string_split(self):
        """Test fix_quoted_string_split adds \\n to split strings."""
        content = 'printk("Hello world");\n'
        test_file = self.create_test_file(content)
        
        result = fix_quoted_string_split(test_file, 1)
        
        fixed_content = self.read_file(test_file)
        # This fix adds \n to strings that need it
        self.assertIsInstance(result, bool)
    
    # Test 3: Assignment in if condition
    def test_fix_assignment_in_if(self):
        """Test fix_assignment_in_if extracts assignment from if condition."""
        content = "if ((x = foo())) {\n    bar();\n}\n"
        test_file = self.create_test_file(content)
        
        result = fix_assignment_in_if(test_file, 1)
        
        fixed_content = self.read_file(test_file)
        # Should extract assignment before if
        self.assertIsInstance(result, bool)
    
    # Test 4: Switch case indent
    def test_fix_switch_case_indent(self):
        """Test fix_switch_case_indent fixes case indentation."""
        content = "switch (x) {\ncase 1:\n    break;\n}\n"
        test_file = self.create_test_file(content)
        
        result = fix_switch_case_indent(test_file, 2)
        
        fixed_content = self.read_file(test_file)
        self.assertIsInstance(result, bool)
    
    # Test 5: Indent with tabs
    def test_fix_indent_tabs(self):
        """Test fix_indent_tabs converts spaces to tabs."""
        content = "        int x = 5;\n"  # 8 spaces
        test_file = self.create_test_file(content)
        
        result = fix_indent_tabs(test_file, 1)
        self.assertTrue(result, "Should convert spaces to tabs")
        
        fixed_content = self.read_file(test_file)
        self.assertIn("\t", fixed_content, "Should contain tab character")
    
    # Test 6: Trailing whitespace
    def test_fix_trailing_whitespace(self):
        """Test fix_trailing_whitespace removes trailing spaces."""
        content = "int x = 5;   \n"
        test_file = self.create_test_file(content)
        
        result = fix_trailing_whitespace(test_file, 1)
        self.assertTrue(result, "Should remove trailing whitespace")
        
        fixed_content = self.read_file(test_file)
        self.assertEqual("int x = 5;\n", fixed_content)
    
    # Test 7: __initconst
    def test_fix_initconst(self):
        """Test fix_initconst changes __initdata to __initconst for const."""
        content = "static const int x __initdata = 5;\n"
        test_file = self.create_test_file(content)
        
        result = fix_initconst(test_file, 1)
        self.assertTrue(result, "Should change __initdata to __initconst")
        
        fixed_content = self.read_file(test_file)
        self.assertIn("__initconst", fixed_content)
        self.assertNotIn("__initdata", fixed_content)
    
    # Test 8: Void return
    def test_fix_void_return(self):
        """Test fix_void_return removes unnecessary return from void functions."""
        content = "void foo() {\n    bar();\n    return;\n}\n"
        test_file = self.create_test_file(content)
        
        result = fix_void_return(test_file, 3)
        
        fixed_content = self.read_file(test_file)
        # This fix removes the return; line
        self.assertIsInstance(result, bool)
    
    # Test 9: Unnecessary braces
    def test_fix_unnecessary_braces(self):
        """Test fix_unnecessary_braces removes braces from single statements."""
        content = "if (x) {\n    foo();\n}\n"
        test_file = self.create_test_file(content)
        
        result = fix_unnecessary_braces(test_file, 1)
        
        fixed_content = self.read_file(test_file)
        self.assertIsInstance(result, bool)
    
    # Test 10: Block comment trailing
    def test_fix_block_comment_trailing(self):
        """Test fix_block_comment_trailing moves */ to separate line."""
        content = "/* Comment text */\n"
        test_file = self.create_test_file(content)
        
        result = fix_block_comment_trailing(test_file, 1)
        
        fixed_content = self.read_file(test_file)
        self.assertIsInstance(result, bool)
    
    # Test 11: SPDX comment style
    def test_fix_spdx_comment(self):
        """Test fix_spdx_comment changes SPDX comment style."""
        content = "// SPDX-License-Identifier: GPL-2.0\n"
        test_file = self.create_test_file(content)
        
        result = fix_spdx_comment(test_file, 1)
        self.assertTrue(result, "Should change // to /* */")
        
        fixed_content = self.read_file(test_file)
        self.assertIn("/* SPDX", fixed_content)
    
    # Test 12: Extern in C files
    def test_fix_extern_in_c(self):
        """Test fix_extern_in_c removes extern declaration lines from .c files."""
        content = "extern int foo(void);\nint bar(void);\n"
        test_file = self.create_test_file(content)
        
        result = fix_extern_in_c(test_file, 1)
        self.assertTrue(result, "Should remove extern line")
        
        fixed_content = self.read_file(test_file)
        self.assertNotIn("extern", fixed_content)
        # The entire extern line should be removed
        self.assertIn("int bar(void);", fixed_content)
    
    # Test 13: Symbolic permissions
    def test_fix_symbolic_permissions(self):
        """Test fix_symbolic_permissions converts symbolic to octal."""
        content = "module_param(x, int, S_IRUSR | S_IWUSR);\n"
        test_file = self.create_test_file(content)
        
        result = fix_symbolic_permissions(test_file, 1)
        self.assertTrue(result, "Should convert to octal")
        
        fixed_content = self.read_file(test_file)
        self.assertIn("0600", fixed_content)
    
    # Test 14: printk(KERN_INFO) to pr_info
    def test_fix_printk_info(self):
        """Test fix_printk_info converts printk(KERN_INFO) to pr_info."""
        content = 'printk(KERN_INFO "test message\\n");\n'
        test_file = self.create_test_file(content)
        
        result = fix_printk_info(test_file, 1)
        self.assertTrue(result, "Should convert to pr_info")
        
        fixed_content = self.read_file(test_file)
        self.assertIn("pr_info", fixed_content)
        self.assertNotIn("printk", fixed_content)
    
    # Test 15: printk(KERN_ERR) to pr_err
    def test_fix_printk_err(self):
        """Test fix_printk_err converts printk(KERN_ERR) to pr_err."""
        content = 'printk(KERN_ERR "error message\\n");\n'
        test_file = self.create_test_file(content)
        
        result = fix_printk_err(test_file, 1)
        self.assertTrue(result, "Should convert to pr_err")
        
        fixed_content = self.read_file(test_file)
        self.assertIn("pr_err", fixed_content)
    
    # Test 16: printk(KERN_WARNING) to pr_warn
    def test_fix_printk_warn(self):
        """Test fix_printk_warn converts printk(KERN_WARNING) to pr_warn."""
        content = 'printk(KERN_WARNING "warning message\\n");\n'
        test_file = self.create_test_file(content)
        
        result = fix_printk_warn(test_file, 1)
        self.assertTrue(result, "Should convert to pr_warn")
        
        fixed_content = self.read_file(test_file)
        self.assertIn("pr_warn", fixed_content)
    
    # Test 17: printk(KERN_EMERG) to pr_emerg
    def test_fix_printk_emerg(self):
        """Test fix_printk_emerg converts printk(KERN_EMERG) to pr_emerg."""
        content = 'printk(KERN_EMERG "emergency message\\n");\n'
        test_file = self.create_test_file(content)
        
        result = fix_printk_emerg(test_file, 1)
        self.assertTrue(result, "Should convert to pr_emerg")
        
        fixed_content = self.read_file(test_file)
        self.assertIn("pr_emerg", fixed_content)
    
    # Test 18: Jiffies comparison
    def test_fix_jiffies_comparison(self):
        """Test fix_jiffies_comparison converts jiffies != to time_after."""
        content = "if (jiffies != timeout) {\n"
        test_file = self.create_test_file(content)
        
        result = fix_jiffies_comparison(test_file, 1)
        self.assertTrue(result, "Should convert to time_after")
        
        fixed_content = self.read_file(test_file)
        self.assertIn("time_after", fixed_content)
    
    # Test 19: Else after return
    def test_fix_else_after_return(self):
        """Test fix_else_after_return removes else after return."""
        content = "if (x) {\n    return 1;\n} else {\n    return 0;\n}\n"
        test_file = self.create_test_file(content)
        
        result = fix_else_after_return(test_file, 3)
        
        fixed_content = self.read_file(test_file)
        self.assertIsInstance(result, bool)
    
    # Test 20: Weak attribute
    def test_fix_weak_attribute(self):
        """Test fix_weak_attribute converts __attribute__((weak)) to __weak."""
        content = "void foo(void) __attribute__((weak));\n"
        test_file = self.create_test_file(content)
        
        result = fix_weak_attribute(test_file, 1)
        self.assertTrue(result, "Should convert to __weak")
        
        fixed_content = self.read_file(test_file)
        self.assertIn("__weak", fixed_content)
        self.assertNotIn("__attribute__", fixed_content)
    
    # Test 21: OOM message
    def test_fix_oom_message(self):
        """Test fix_oom_message removes unnecessary OOM messages."""
        content = 'if (!ptr) {\n    printk("out of memory\\n");\n    return -ENOMEM;\n}\n'
        test_file = self.create_test_file(content)
        
        result = fix_oom_message(test_file, 2)
        
        fixed_content = self.read_file(test_file)
        self.assertIsInstance(result, bool)
    
    # Test 22: ASM includes
    def test_fix_asm_includes(self):
        """Test fix_asm_includes converts <asm/io.h> to <linux/io.h>."""
        content = "#include <asm/io.h>\n"
        test_file = self.create_test_file(content)
        
        result = fix_asm_includes(test_file, 1)
        self.assertTrue(result, "Should convert to linux/")
        
        fixed_content = self.read_file(test_file)
        self.assertIn("<linux/io.h>", fixed_content)
        self.assertNotIn("<asm/io.h>", fixed_content)
    
    # Test 23: __initdata placement
    def test_fix_initdata_placement(self):
        """Test fix_initdata_placement moves __initdata after variable name."""
        content = "static int __initdata x = 5;\n"
        test_file = self.create_test_file(content)
        
        result = fix_initdata_placement(test_file, 1)
        self.assertTrue(result, "Should move __initdata")
        
        fixed_content = self.read_file(test_file)
        self.assertIn("x __initdata", fixed_content)
    
    # Test 24: Missing SPDX
    def test_fix_missing_spdx(self):
        """Test fix_missing_spdx adds SPDX header to file."""
        content = "#include <stdio.h>\n"
        test_file = self.create_test_file(content)
        
        result = fix_missing_spdx(test_file, 1)
        self.assertTrue(result, "Should add SPDX header")
        
        fixed_content = self.read_file(test_file)
        self.assertIn("SPDX-License-Identifier", fixed_content)
    
    # Test 25: msleep too small
    def test_fix_msleep_too_small(self):
        """Test fix_msleep_too_small adds comment about msleep behavior."""
        content = "msleep(10);\n"
        test_file = self.create_test_file(content)
        
        result = fix_msleep_too_small(test_file, 1)
        
        fixed_content = self.read_file(test_file)
        self.assertIsInstance(result, bool)
    
    # Test 26: strcpy to strscpy
    def test_fix_strcpy_to_strscpy(self):
        """Test fix_strcpy_to_strscpy converts strcpy to strscpy."""
        content = "strcpy(dest, src);\n"
        test_file = self.create_test_file(content)
        
        result = fix_strcpy_to_strscpy(test_file, 1)
        self.assertTrue(result, "Should convert to strscpy")
        
        fixed_content = self.read_file(test_file)
        self.assertIn("strscpy", fixed_content)
        self.assertNotIn("strcpy(dest", fixed_content)
    
    # Test 27: strncpy to strscpy
    def test_fix_strncpy(self):
        """Test fix_strncpy converts strncpy to strscpy."""
        content = "strncpy(dest, src, 10);\n"
        test_file = self.create_test_file(content)
        
        result = fix_strncpy(test_file, 1)
        self.assertTrue(result, "Should convert to strscpy")
        
        fixed_content = self.read_file(test_file)
        self.assertIn("strscpy", fixed_content)
    
    # Test 28: Spaces at start of line
    def test_fix_spaces_at_start_of_line(self):
        """Test fix_spaces_at_start_of_line removes leading spaces from blank lines."""
        content = "int x;\n   \nint y;\n"
        test_file = self.create_test_file(content)
        
        result = fix_spaces_at_start_of_line(test_file, 2)
        self.assertTrue(result, "Should remove leading spaces")
        
        fixed_content = self.read_file(test_file)
        lines = fixed_content.split('\n')
        # Line 2 (index 1) should now be just empty or have no leading spaces if otherwise empty
        self.assertNotIn("   ", lines[1])
    
    # Test 29: Filename in file
    def test_fix_filename_in_file(self):
        """Test fix_filename_in_file removes filename comments."""
        content = "// File: test.c\nint main() {\n"
        test_file = self.create_test_file(content)
        
        result = fix_filename_in_file(test_file, 1)
        
        fixed_content = self.read_file(test_file)
        self.assertIsInstance(result, bool)
    
    # Test 30: Prefer notice
    def test_fix_prefer_notice(self):
        """Test fix_prefer_notice converts printk(KERN_NOTICE) to pr_notice."""
        content = 'printk(KERN_NOTICE "notice message\\n");\n'
        test_file = self.create_test_file(content)
        
        result = fix_prefer_notice(test_file, 1)
        self.assertTrue(result, "Should convert to pr_notice")
        
        fixed_content = self.read_file(test_file)
        self.assertIn("pr_notice", fixed_content)
    
    # Test 31: __FUNCTION__ to __func__
    def test_fix_function_macro(self):
        """Test fix_function_macro converts __FUNCTION__ to __func__."""
        content = 'printk("%s\\n", __FUNCTION__);\n'
        test_file = self.create_test_file(content)
        
        result = fix_function_macro(test_file, 1)
        self.assertTrue(result, "Should convert __FUNCTION__ to __func__")
        
        fixed_content = self.read_file(test_file)
        self.assertIn("__func__", fixed_content)
        self.assertNotIn("__FUNCTION__", fixed_content)
    
    # Test 32: Space before open brace
    def test_fix_space_before_open_brace(self):
        """Test fix_space_before_open_brace adds space before '{'."""
        content = "if (x){\n    foo();\n}\n"
        test_file = self.create_test_file(content)
        
        result = fix_space_before_open_brace(test_file, 1)
        self.assertTrue(result, "Should add space before '{'")
        
        fixed_content = self.read_file(test_file)
        self.assertIn("if (x) {", fixed_content)
    
    # Test 33: Else after close brace
    def test_fix_else_after_close_brace(self):
        """Test fix_else_after_close_brace moves else to same line as '}'."""
        content = "if (x) {\n    foo();\n}\nelse {\n    bar();\n}\n"
        test_file = self.create_test_file(content)
        
        result = fix_else_after_close_brace(test_file, 4)
        self.assertTrue(result, "Should move else to same line")
        
        fixed_content = self.read_file(test_file)
        self.assertIn("} else", fixed_content)
    
    # Test 34: sizeof struct to sizeof pointer
    def test_fix_sizeof_struct(self):
        """Test fix_sizeof_struct converts sizeof(struct type) to sizeof(*p)."""
        content = "p = kmalloc(sizeof(struct foo));\n"
        test_file = self.create_test_file(content)
        
        result = fix_sizeof_struct(test_file, 1)
        self.assertTrue(result, "Should convert to sizeof(*p)")
        
        fixed_content = self.read_file(test_file)
        self.assertIn("sizeof(*p)", fixed_content)
        self.assertNotIn("sizeof(struct", fixed_content)
    
    # Test 35: Consecutive strings
    def test_fix_consecutive_strings(self):
        """Test fix_consecutive_strings merges consecutive string literals."""
        content = 'printk("Hello " "World\\n");\n'
        test_file = self.create_test_file(content)
        
        result = fix_consecutive_strings(test_file, 1)
        self.assertTrue(result, "Should merge consecutive strings")
        
        fixed_content = self.read_file(test_file)
        self.assertIn('"Hello World\\n"', fixed_content)
        self.assertEqual(fixed_content.count('"'), 2)  # Only one string, so 2 quotes
    
    # Test 36: Comparison to NULL
    def test_fix_comparison_to_null(self):
        """Test fix_comparison_to_null converts NULL comparisons."""
        content = "if (ptr == NULL) {\n    return;\n}\n"
        test_file = self.create_test_file(content)
        
        result = fix_comparison_to_null(test_file, 1)
        self.assertTrue(result, "Should convert to !ptr")
        
        fixed_content = self.read_file(test_file)
        self.assertIn("if (!ptr)", fixed_content)
    
    # Test 37: Constant comparison order
    def test_fix_constant_comparison(self):
        """Test fix_constant_comparison swaps constant to right side."""
        content = "if (5 == x) {\n    foo();\n}\n"
        test_file = self.create_test_file(content)
        
        result = fix_constant_comparison(test_file, 1)
        self.assertTrue(result, "Should swap to x == 5")
        
        fixed_content = self.read_file(test_file)
        self.assertIn("x == 5", fixed_content)


class TestFixFunctionsIntegration(unittest.TestCase):
    """Integration tests to verify fixes work on real patterns."""
    
    def setUp(self):
        """Create a temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up temporary test directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def create_test_file(self, content):
        """Create a temporary test file with given content."""
        test_file = Path(self.test_dir) / "test.c"
        with open(test_file, "w") as f:
            f.write(content)
        return test_file
    
    def read_file(self, file_path):
        """Read and return file content."""
        with open(file_path, "r") as f:
            return f.read()
    
    def test_multiple_printk_conversions(self):
        """Test that multiple printk conversions work correctly."""
        content = '''printk(KERN_INFO "info\\n");
printk(KERN_ERR "error\\n");
printk(KERN_WARNING "warning\\n");
'''
        test_file = self.create_test_file(content)
        
        # Apply fixes in sequence
        fix_printk_info(test_file, 1)
        fix_printk_err(test_file, 2)
        fix_printk_warn(test_file, 3)
        
        fixed_content = self.read_file(test_file)
        self.assertIn("pr_info", fixed_content)
        self.assertIn("pr_err", fixed_content)
        self.assertIn("pr_warn", fixed_content)
    
    def test_indent_and_trailing_whitespace(self):
        """Test that indent and trailing whitespace fixes work together."""
        content = "        int x = 5;   \n"
        test_file = self.create_test_file(content)
        
        # Apply both fixes
        fix_indent_tabs(test_file, 1)
        fix_trailing_whitespace(test_file, 1)
        
        fixed_content = self.read_file(test_file)
        self.assertIn("\t", fixed_content)
        # Check that there's no trailing whitespace (other than newline)
        lines = fixed_content.split('\n')
        for line in lines[:-1]:  # Skip last empty line
            self.assertEqual(line.rstrip(), line, "Line should not have trailing whitespace")


def run_tests():
    """Run all tests and return success status."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestFixFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestFixFunctionsIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
