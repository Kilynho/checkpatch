#!/usr/bin/env python3
"""
Script unificado de revisión, testing y análisis de cobertura.

Incluye:
- Suite de tests unificada (compilation, fixes, integration)
- Análisis de cobertura de tipos de checkpatch
- Análisis de cobertura real basado en JSON

Ejecutar:
  python3 scripts/review_and_test.py              # Ejecutar tests
  python3 scripts/review_and_test.py --coverage   # Análisis de cobertura teórica
  python3 scripts/review_and_test.py --real       # Análisis de cobertura real
  python3 scripts/review_and_test.py --all        # Ejecutar todo
"""

import json
import subprocess
import sys
import unittest
import tempfile
import os
import re
from pathlib import Path
from collections import defaultdict
import shutil

# Añadir directorio raíz al path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Import modules
from compile import (
    CompilationResult,
    summarize_results,
    save_json_report,
    restore_backups
)

from core import (
    fix_missing_blank_line,
    fix_quoted_string_split,
    fix_switch_case_indent,
    fix_indent_tabs,
    fix_trailing_whitespace,
    fix_initconst,
    fix_void_return,
    fix_unnecessary_braces,
    fix_block_comment_trailing,
    fix_spdx_comment,
    fix_extern_in_c,
    fix_symbolic_permissions,
    fix_printk_info,
    fix_printk_err,
    fix_printk_warn,
    fix_printk_emerg,
    fix_jiffies_comparison,
    fix_else_after_return,
    fix_weak_attribute,
    fix_oom_message,
    fix_asm_includes,
    fix_initdata_placement,
    fix_missing_spdx,
    fix_msleep_too_small,
    fix_strcpy_to_strscpy,
    fix_strncpy,
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

from engine import AUTO_FIX_RULES


# ============================================================================
# COVERAGE ANALYSIS DATA
# ============================================================================

# Lista completa de los 227 tipos de checkpatch con su clasificación
CHECKPATCH_TYPES = {
    'ERROR': [
        'ALLOC_ARRAY_ARGS', 'ALLOC_SIZEOF_STRUCT', 'ARCH_DEFINES',
        'ARCH_INCLUDE_LINUX', 'ASSIGN_IN_IF', 'AVOID_BUG', 'BAD_FIXES_TAG',
        'BAD_REPORTED_BY_LINK', 'BAD_SIGN_OFF', 'BAD_STABLE_ADDRESS_STYLE',
        'BRACKET_SPACE', 'C99_COMMENTS', 'CODE_INDENT', 'COMMIT_COMMENT_SYMBOL',
        'COMMIT_LOG_LONG_LINE', 'COMMIT_LOG_USE_LINK', 'COMMIT_LOG_VERSIONING',
        'COMMIT_LOG_WRONG_LINK', 'COMMIT_MESSAGE', 'COMPLEX_MACRO',
        'CONFIG_DESCRIPTION', 'CONST_CONST', 'CORRUPTED_PATCH', 'CVS_KEYWORD',
        'DATE_TIME', 'DEVICE_ATTR_PERMS', 'DIFF_IN_COMMIT_MSG',
        'DOS_LINE_ENDINGS', 'DO_WHILE_MACRO_WITH_TRAILING_SEMICOLON',
        'DT_SCHEMA_BINDING_PATCH', 'DT_SPLIT_BINDING_PATCH',
        'DUPLICATED_SYSCTL_CONST', 'ELSE_AFTER_BRACE', 'EMAIL_SUBJECT',
        'EMBEDDED_FILENAME', 'ENOSYS', 'EXECUTE_PERMISSIONS',
        'EXPORTED_WORLD_WRITABLE', 'FILE_PATH_CHANGES', 'FROM_SIGN_OFF_MISMATCH',
        'FSF_MAILING_ADDRESS', 'GERRIT_CHANGE_ID', 'GIT_COMMIT_ID',
        'HEXADECIMAL_BOOLEAN_TEST', 'IF_0', 'INITIALISED_STATIC',
        'INIT_ATTRIBUTE', 'INVALID_UTF8', 'KREALLOC_ARG_REUSE',
        'LEADING_SPACE', 'LINUX_VERSION_CODE', 'MACRO_ARG_PRECEDENCE',
        'MACRO_ARG_REUSE', 'MALFORMED_INCLUDE', 'MISSING_EOF_NEWLINE',
        'MISSING_FIXES_TAG', 'MISSING_SIGN_OFF', 'MODIFIED_INCLUDE_ASM',
        'MULTILINE_DEREFERENCE', 'MULTISTATEMENT_MACRO_USE_DO_WHILE',
        'NEW_TYPEDEFS', 'NOT_UNIFIED_DIFF', 'NO_AUTHOR_SIGN_OFF',
        'OPEN_BRACE', 'OPEN_ENDED_LINE', 'PATCH_PREFIX', 'POINTER_LOCATION',
        'QUOTED_WHITESPACE_BEFORE_NEWLINE', 'RETURN_PARENTHESES',
        'SELF_ASSIGNMENT', 'SIZEOF_ADDRESS', 'SPACE_BEFORE_TAB', 'SPACING',
        'SPDX_LICENSE_TAG', 'STORAGE_CLASS', 'SUSPECT_CODE_INDENT',
        'SUSPECT_COMMA_SEMICOLON', 'SWITCH_CASE_INDENT_LEVEL',
        'TRAILING_SEMICOLON', 'TRAILING_STATEMENTS', 'TRAILING_WHITESPACE',
        'UNDOCUMENTED_DT_STRING', 'UNDOCUMENTED_SETUP', 'UNKNOWN_COMMIT_ID',
        'UNNECESSARY_PARENTHESES', 'UNSPECIFIED_INT', 'UTF8_BEFORE_PATCH',
        'WHILE_AFTER_BRACE', 'WHITESPACE_AFTER_LINE_CONTINUATION',
    ],
    'WARNING': [
        'ALLOC_WITH_MULTIPLY', 'ARRAY_SIZE', 'ASSIGNMENT_CONTINUATIONS',
        'AVOID_EXTERNS', 'AVOID_L_PREFIX', 'BIT_MACRO', 'BLOCK_COMMENT_STYLE',
        'BOOL_COMPARISON', 'BRACES', 'CAMELCASE', 'COMPARISON_TO_NULL',
        'CONCATENATED_STRING', 'CONSIDER_COMPLETION', 'CONSIDER_KSTRTO',
        'CONSTANT_COMPARISON', 'CONSTANT_CONVERSION', 'CONST_READ_MOSTLY',
        'CONST_STRUCT', 'DATA_RACE', 'DEEP_INDENTATION', 'DEFAULT_NO_BREAK',
        'DEFINE_ARCH_HAS', 'DEPRECATED_API', 'DEVICE_ATTR_FUNCTIONS',
        'DEVICE_ATTR_RO', 'DEVICE_ATTR_RW', 'DEVICE_ATTR_WO', 'ENOTSUPP',
        'EXPORT_SYMBOL', 'FLEXIBLE_ARRAY', 'FUNCTION_ARGUMENTS',
        'FUNCTION_WITHOUT_ARGS', 'GLOBAL_INITIALISERS', 'HOTPLUG_SECTION',
        'IF_1', 'INCLUDE_LINUX', 'INDENTED_LABEL', 'INLINE', 'INLINE_LOCATION',
        'IN_ATOMIC', 'IS_ENABLED_CONFIG', 'JIFFIES_COMPARISON', 'LIKELY_MISUSE',
        'LINE_CONTINUATIONS', 'LINE_SPACING', 'LOCKDEP', 'LOGGING_CONTINUATION',
        'LOGICAL_CONTINUATIONS', 'LONG_LINE', 'LONG_LINE_COMMENT',
        'LONG_LINE_STRING', 'LONG_UDELAY', 'MACRO_ARG_UNUSED',
        'MACRO_WITH_FLOW_CONTROL', 'MAINTAINERS_STYLE', 'MASK_THEN_SHIFT',
        'MEMORY_BARRIER', 'MEMSET', 'MINMAX', 'MISORDERED_TYPE',
        'MISPLACED_INIT', 'MISSING_SENTINEL', 'MODULE_LICENSE', 'MSLEEP',
        'MULTIPLE_ASSIGNMENTS', 'MULTIPLE_DECLARATION', 'NAKED_SSCANF',
        'NON_OCTAL_PERMISSIONS', 'NR_CPUS', 'OBSOLETE', 'ONE_SEMICOLON',
        'OOM_MESSAGE', 'PARENTHESIS_ALIGNMENT', 'PREFER_DEFINED_ATTRIBUTE_MACRO',
        'PREFER_DEV_LEVEL', 'PREFER_ETHER_ADDR_COPY', 'PREFER_ETHER_ADDR_EQUAL',
        'PREFER_ETHTOOL_PUTS', 'PREFER_ETH_BROADCAST_ADDR',
        'PREFER_ETH_ZERO_ADDR', 'PREFER_FALLTHROUGH', 'PREFER_IS_ENABLED',
        'PREFER_KERNEL_TYPES', 'PREFER_LORE_ARCHIVE', 'PREFER_PR_LEVEL',
        'PREFER_SEQ_PUTS', 'PRINTF_0XDECIMAL', 'PRINTF_L', 'PRINTF_Z',
        'PRINTK_RATELIMITED', 'PRINTK_WITHOUT_KERN_LEVEL', 'REPEATED_WORD',
        'RETURN_VOID', 'SINGLE_STATEMENT_DO_WHILE_MACRO', 'SIZEOF_PARENTHESIS',
        'SPLIT_STRING', 'SSCANF_TO_KSTRTO', 'STATIC_CONST',
        'STATIC_CONST_CHAR_ARRAY', 'STRCPY', 'STRING_FRAGMENTS', 'STRLCPY',
        'STRNCPY', 'SYMBOLIC_PERMS', 'SYSFS_EMIT', 'TABSTOP', 'TEST_ATTR',
        'TEST_NOT_ATTR', 'TEST_NOT_TYPE', 'TEST_TYPE', 'TRACE_PRINTK',
        'TRACING_LOGGING', 'TYPECAST_INT_CONSTANT', 'TYPO_SPELLING',
        'UAPI_INCLUDE', 'UNCOMMENTED_DEFINITION', 'UNCOMMENTED_RGMII_MODE',
        'UNNECESSARY_BREAK', 'UNNECESSARY_CASTS', 'UNNECESSARY_ELSE',
        'UNNECESSARY_INT', 'UNNECESSARY_KERN_LEVEL', 'UNNECESSARY_MODIFIER',
        'USE_DEVICE_INITCALL', 'USE_FUNC', 'USE_LOCKDEP', 'USE_NEGATIVE_ERRNO',
        'USE_RELATIVE_PATH', 'USE_SPINLOCK_T', 'USLEEP_RANGE', 'VOLATILE',
        'VSPRINTF_POINTER_EXTENSION', 'VSPRINTF_SPECIFIER_PX',
        'WAITQUEUE_ACTIVE', 'WEAK_DECLARATION', 'YIELD',
    ],
}

# Mapeo de mensajes a tipos
MESSAGE_TO_TYPE = {
    "Missing a blank line after declarations": "LINE_SPACING",
    "quoted string split across lines": "SPLIT_STRING",
    "space required after that ','": "SPACING",
    "space prohibited before that ','": "SPACING",
    "space prohibited before that close parenthesis ')'": "SPACING",
    "spaces required around that '='": "SPACING",
    "code indent should use tabs where possible": "CODE_INDENT",
    "trailing whitespace": "TRAILING_WHITESPACE",
    "do not use assignment in if condition": "ASSIGN_IN_IF",
    "Use of const init definition must use __initconst": "MISPLACED_INIT",
    "space prohibited after that open parenthesis '('": "SPACING",
    "space before tabs": "SPACE_BEFORE_TAB",
    "void function return statements are not generally useful": "RETURN_VOID",
    "braces {} are not necessary for single statement blocks": "BRACES",
    "Block comments use a trailing */ on a separate line": "BLOCK_COMMENT_STYLE",
    "char * array declaration might be better as static const": "STATIC_CONST_CHAR_ARRAY",
    "Prefer 'unsigned int' to bare use of 'unsigned'": "UNSPECIFIED_INT",
    "externs should be avoided in .c files": "AVOID_EXTERNS",
    "simple_strtoul is obsolete, use kstrtoul instead": "CONSIDER_KSTRTO",
    "simple_strtol is obsolete, use kstrtol instead": "CONSIDER_KSTRTO",
    "Prefer using": "USE_FUNC",
    "else is not generally useful after a break or return": "UNNECESSARY_ELSE",
    "Prefer __weak over __attribute__((weak))": "WEAK_DECLARATION",
    "Possible unnecessary 'out of memory' message": "OOM_MESSAGE",
    "__initdata should be placed after": "MISPLACED_INIT",
    "msleep < 20ms can sleep for up to 20ms": "MSLEEP",
    "Prefer strscpy over strcpy": "STRCPY",
    "Prefer using strscpy instead of strncpy": "STRNCPY",
    "switch and case should be at the same indent": "SWITCH_CASE_INDENT_LEVEL",
    "Avoid logging continuation uses where feasible": "LOGGING_CONTINUATION",
    "It's generally not useful to have the filename in the file": "EMBEDDED_FILENAME",
    "please, no spaces at the start of a line": "LEADING_SPACE",
}

PRINTK_PATTERNS = {
    r"Prefer.*printk\(KERN_INFO": "PREFER_PR_LEVEL",
    r"Prefer.*printk\(KERN_ERR": "PREFER_PR_LEVEL",
    r"Prefer.*printk\(KERN_WARNING": "PREFER_PR_LEVEL",
    r"Prefer.*printk\(KERN_DEBUG": "PREFER_PR_LEVEL",
    r"Prefer.*printk\(KERN_EMERG": "PREFER_PR_LEVEL",
    r"Prefer.*printk\(KERN_NOTICE": "PREFER_PR_LEVEL",
    r"printk\(\) should include KERN": "PRINTK_WITHOUT_KERN_LEVEL",
    r"Comparing jiffies": "JIFFIES_COMPARISON",
    r"Symbolic permissions.*are not preferred": "SYMBOLIC_PERMS",
    r"Use #include <linux/.+> instead of <asm/.+>": "ARCH_INCLUDE_LINUX",
    r"Missing or malformed SPDX": "SPDX_LICENSE_TAG",
    r"Improper SPDX comment style": "SPDX_LICENSE_TAG",
}


# ============================================================================
# COVERAGE ANALYSIS FUNCTIONS
# ============================================================================

def extract_type_from_message(message):
    """Extrae el tipo de checkpatch de un mensaje."""
    clean_msg = message.replace("ERROR:", "").replace("WARNING:", "").strip()
    
    for pattern, msg_type in MESSAGE_TO_TYPE.items():
        if pattern in clean_msg:
            return msg_type
    
    for pattern, msg_type in PRINTK_PATTERNS.items():
        if re.search(pattern, clean_msg):
            return msg_type
    
    return None


def analyze_theoretical_coverage():
    """Analiza cobertura teórica basada en tipos implementados."""
    covered_patterns = set()
    for fix_name, fix_func in AUTO_FIX_RULES.items():
        if 'spacing' in fix_name.lower():
            covered_patterns.add('SPACING')
        elif 'return_void' in fix_name.lower():
            covered_patterns.add('RETURN_VOID')
        elif 'initdata' in fix_name.lower():
            covered_patterns.add('MISPLACED_INIT')
        elif 'jiffies' in fix_name.lower():
            covered_patterns.add('JIFFIES_COMPARISON')
        elif 'printk' in fix_name.lower():
            covered_patterns.update(['PRINTK_WITHOUT_KERN_LEVEL', 'PREFER_PR_LEVEL'])
    
    print("\n" + "="*80)
    print("ANÁLISIS DE COBERTURA TEÓRICA")
    print("="*80)
    
    for severity in ['ERROR', 'WARNING']:
        types_list = CHECKPATCH_TYPES[severity]
        covered = [t for t in types_list if t in covered_patterns]
        uncovered = [t for t in types_list if t not in covered_patterns]
        
        pct = (len(covered) / len(types_list) * 100) if types_list else 0
        
        print(f"\n{severity}S: {len(covered)}/{len(types_list)} cubiertos ({pct:.1f}%)")
        print("-" * 80)
        
        if covered:
            print(f"\n✅ CUBIERTOS ({len(covered)}):")
            for t in sorted(covered)[:10]:
                print(f"  - {t}")
            if len(covered) > 10:
                print(f"  ... y {len(covered) - 10} más")
    
    total_types = len(CHECKPATCH_TYPES['ERROR']) + len(CHECKPATCH_TYPES['WARNING'])
    total_covered = len(covered_patterns)
    total_pct = (total_covered / total_types * 100) if total_types else 0
    
    print("\n" + "="*80)
    print(f"RESUMEN: {total_covered}/{total_types} tipos cubiertos ({total_pct:.1f}%)")
    print("="*80)


def analyze_real_coverage():
    """Analiza cobertura real basada en json/checkpatch.json."""
    json_path = Path(root_dir) / "json" / "checkpatch.json"
    
    if not json_path.exists():
        print(f"\n❌ No se encontró {json_path}")
        print("   Ejecuta primero: ./run o ./main.py --analyze")
        return
    
    with open(json_path) as f:
        data = json.load(f)
    
    error_types = defaultdict(int)
    warning_types = defaultdict(int)
    unknown = set()
    
    for item in data:
        for issue in item.get('error', []):
            msg = issue['message']
            msg_type = extract_type_from_message(msg)
            if msg_type:
                error_types[msg_type] += 1
            else:
                unknown.add(('ERROR', msg))
        
        for issue in item.get('warning', []):
            msg = issue['message']
            msg_type = extract_type_from_message(msg)
            if msg_type:
                warning_types[msg_type] += 1
            else:
                unknown.add(('WARNING', msg))
    
    implemented_types = set()
    for msg_key in AUTO_FIX_RULES.keys():
        msg_type = extract_type_from_message(msg_key)
        if msg_type:
            implemented_types.add(msg_type)
    
    found_error_types = set(error_types.keys())
    found_warning_types = set(warning_types.keys())
    
    print("\n" + "="*80)
    print("ANÁLISIS DE COBERTURA REAL (json/checkpatch.json)")
    print("="*80)
    
    print(f"\n📊 ERRORES: {sum(error_types.values())} casos, {len(found_error_types)} tipos")
    print("-" * 80)
    covered_errors = found_error_types & implemented_types
    uncovered_errors = found_error_types - implemented_types
    
    if covered_errors:
        print(f"\n✅ CON FIX ({len(covered_errors)}):")
        for t in sorted(covered_errors):
            print(f"  - {t}: {error_types[t]} casos")
    
    if uncovered_errors:
        print(f"\n❌ SIN FIX ({len(uncovered_errors)}):")
        for t in sorted(uncovered_errors):
            print(f"  - {t}: {error_types[t]} casos")
    
    print(f"\n📊 WARNINGS: {sum(warning_types.values())} casos, {len(found_warning_types)} tipos")
    print("-" * 80)
    covered_warnings = found_warning_types & implemented_types
    uncovered_warnings = found_warning_types - implemented_types
    
    if covered_warnings:
        print(f"\n✅ CON FIX ({len(covered_warnings)}):")
        for t in sorted(covered_warnings):
            print(f"  - {t}: {warning_types[t]} casos")
    
    if uncovered_warnings:
        print(f"\n❌ SIN FIX ({len(uncovered_warnings)}):")
        for t in sorted(uncovered_warnings):
            print(f"  - {t}: {warning_types[t]} casos")
    
    if unknown:
        print(f"\n⚠️  MENSAJES SIN MAPEAR ({len(unknown)}):")
        for severity, msg in list(unknown)[:5]:
            print(f"  [{severity}] {msg[:70]}...")
    
    total_found = len(found_error_types) + len(found_warning_types)
    total_covered = len(covered_errors) + len(covered_warnings)
    pct = (total_covered / total_found * 100) if total_found else 0
    
    print("\n" + "="*80)
    print(f"RESUMEN: {total_covered}/{total_found} tipos cubiertos ({pct:.1f}%)")
    print(f"  - Errores: {len(covered_errors)}/{len(found_error_types)}")
    print(f"  - Warnings: {len(covered_warnings)}/{len(found_warning_types)}")
    print("="*80)


# ============================================================================
# TEST SUITE
# ============================================================================

class TestCompilation(unittest.TestCase):
    """Tests for compilation module."""
    
    def test_compilation_result_success(self):
        """Test creating a successful compilation result."""
        result = CompilationResult("/path/to/file.c", True, 1.5, stdout="output")
        self.assertTrue(result.success)
        self.assertEqual(result.file_path, "/path/to/file.c")
        self.assertEqual(result.duration, 1.5)
    
    def test_compilation_result_failure(self):
        """Test creating a failed compilation result."""
        result = CompilationResult("/path/to/file.c", False, 2.0, 
                                  error_message="error: undefined reference")
        self.assertFalse(result.success)
        self.assertEqual(result.error_message, "error: undefined reference")
    
    def test_to_dict(self):
        """Test converting result to dictionary."""
        result = CompilationResult("/path/to/file.c", True, 1.0)
        data = result.to_dict()
        self.assertIsInstance(data, dict)
        self.assertEqual(data["file"], "/path/to/file.c")
        self.assertTrue(data["success"])
    
    def test_summarize_results(self):
        """Test result summarization."""
        results = [
            CompilationResult("/file1.c", True, 1.0),
            CompilationResult("/file2.c", False, 2.0),
            CompilationResult("/file3.c", True, 1.5)
        ]
        summary = summarize_results(results)
        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["successful"], 2)
        self.assertEqual(summary["failed"], 1)
    
    def test_save_json_report(self):
        """Test saving compilation results to JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "compile.json"
            results = [
                CompilationResult("/file1.c", True, 1.0),
                CompilationResult("/file2.c", False, 2.0, error_message="error")
            ]
            save_json_report(results, output_path)
            self.assertTrue(output_path.exists())
            
            with open(output_path) as f:
                data = json.load(f)
            self.assertIn("summary", data)
            self.assertIn("results", data)
            self.assertEqual(len(data["results"]), 2)
    
    def test_restore_backups(self):
        """Test restoring files from backups."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.c"
            test_file.write_text("modified content")
            backup_file = Path(tmpdir) / "test.c.bak"
            backup_file.write_text("original content")
            
            restore_backups([test_file])
            self.assertEqual(test_file.read_text(), "original content")


class TestFixFunctions(unittest.TestCase):
    """Tests for checkpatch autofix functions."""
    
    def setUp(self):
        """Create a temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary test directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def create_test_file(self, content):
        """Create a temporary test file and return its path."""
        test_file = Path(self.test_dir) / "test.c"
        with open(test_file, "w") as f:
            f.write(content)
        return test_file
    
    def read_file(self, file_path):
        """Read and return file content."""
        with open(file_path, "r") as f:
            return f.read()
    
    def test_fix_trailing_whitespace(self):
        """Test fix_trailing_whitespace removes trailing spaces."""
        content = "int x = 5;   \n"
        test_file = self.create_test_file(content)
        result = fix_trailing_whitespace(test_file, 1)
        self.assertTrue(result)
        fixed_content = self.read_file(test_file)
        self.assertEqual("int x = 5;\n", fixed_content)
    
    def test_fix_indent_tabs(self):
        """Test fix_indent_tabs converts spaces to tabs."""
        content = "        int x = 5;\n"
        test_file = self.create_test_file(content)
        result = fix_indent_tabs(test_file, 1)
        self.assertTrue(result)
        fixed_content = self.read_file(test_file)
        self.assertIn("\t", fixed_content)
    
    def test_fix_initconst(self):
        """Test fix_initconst changes __initdata to __initconst for const."""
        content = "static const int x __initdata = 5;\n"
        test_file = self.create_test_file(content)
        result = fix_initconst(test_file, 1)
        self.assertTrue(result)
        fixed_content = self.read_file(test_file)
        self.assertIn("__initconst", fixed_content)
        self.assertNotIn("__initdata", fixed_content)
    
    def test_fix_printk_info(self):
        """Test fix_printk_info converts printk(KERN_INFO) to pr_info."""
        content = 'printk(KERN_INFO "test");\n'
        test_file = self.create_test_file(content)
        result = fix_printk_info(test_file, 1)
        self.assertIsInstance(result, bool)
    
    def test_fix_strcpy_to_strscpy(self):
        """Test fix_strcpy_to_strscpy converts strcpy to strscpy."""
        content = 'strcpy(dest, src);\n'
        test_file = self.create_test_file(content)
        result = fix_strcpy_to_strscpy(test_file, 1)
        self.assertIsInstance(result, bool)


def run_command(cmd, cwd=None):
    """Execute command and return result."""
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


class TestIntegration(unittest.TestCase):
    """Integration test for full workflow."""
    
    def test_full_integration(self):
        """Test complete workflow: restore, analyze, fix, compile."""
        kernel_path = Path("/home/kilynho/src/kernel/linux")
        checkpatch_path = Path(root_dir)
        
        if not kernel_path.exists():
            self.skipTest("Kernel source not found")
        
        print("\n" + "=" * 80)
        print("TEST DE INTEGRACIÓN - CHECKPATCH AUTOFIX")
        print("=" * 80)
        
        print("\n[1/4] Restaurando archivos originales desde git...")
        ret, out, err = run_command("git checkout init/", cwd=kernel_path)
        if ret != 0:
            print(f"❌ Error restaurando archivos: {err}")
            self.fail("Failed to restore files")
        print("✓ Archivos restaurados")
        
        print("\n[2/4] Ejecutando análisis y fixes...")
        ret, out, err = run_command("./run 2>&1", cwd=checkpatch_path)
        if ret != 0:
            print(f"❌ Error ejecutando ./run: {err}")
            print(f"Output: {out}")
        
        print("\n[3/4] Validando resultados...")
        try:
            fixed_json = checkpatch_path / "json" / "fixed.json"
            with open(fixed_json) as f:
                data = json.load(f)
            
            total_warnings = 0
            total_fixed = 0
            
            for file_path, issues in data.items():
                for w in issues.get('warning', []):
                    total_warnings += 1
                    if w.get('fixed'):
                        total_fixed += 1
            
            print(f"✓ Total warnings: {total_warnings}")
            print(f"✓ Warnings corregidos: {total_fixed} ({100*total_fixed/total_warnings:.1f}%)")
            
        except Exception as e:
            print(f"❌ Error validando JSON: {e}")
            self.fail("Failed to validate JSON")
        
        print("\n[4/4] Validando archivos modificados...")
        ret, out, err = run_command("git status --short init/", cwd=kernel_path)
        modified_files = []
        for line in out.split('\n'):
            if line.strip() and line.startswith(' M'):
                modified_files.append(line.strip().split()[1])
        
        print(f"✓ Archivos modificados: {len(modified_files)}")
        
        syntax_errors = []
        for file_path in modified_files:
            if file_path.endswith('.c'):
                full_path = kernel_path / file_path
                try:
                    with open(full_path) as f:
                        content = f.read()
                        open_braces = content.count('{')
                        close_braces = content.count('}')
                        if open_braces != close_braces:
                            syntax_errors.append(f"{file_path}: {{ {open_braces} vs }} {close_braces}")
                except Exception as e:
                    syntax_errors.append(f"{file_path}: {e}")
        
        if syntax_errors:
            print(f"\n⚠️  Posibles problemas de sintaxis:")
            for err in syntax_errors:
                print(f"   - {err}")
        else:
            print("✓ No se detectaron problemas de sintaxis evidentes")
        
        print("\n" + "=" * 80)
        if total_fixed >= 100 and not syntax_errors:
            print("✅ TEST EXITOSO")
            print(f"   {total_fixed}/{total_warnings} warnings corregidos ({100*total_fixed/total_warnings:.1f}%)")
            print("=" * 80)
        else:
            print("⚠️  TEST COMPLETADO CON ADVERTENCIAS")
            if total_fixed < 100:
                print(f"   - Solo {total_fixed}/{total_warnings} warnings corregidos (esperado: ≥100)")
            if syntax_errors:
                print(f"   - Se detectaron {len(syntax_errors)} posibles problemas de sintaxis")
            print("=" * 80)
            self.fail("Integration test did not meet criteria")


# ============================================================================
# MAIN
# ============================================================================

def run_tests():
    """Ejecuta la suite de tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestCompilation))
    suite.addTests(loader.loadTestsFromTestCase(TestFixFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return {
        'testsRun': result.testsRun,
        'failures': len(result.failures),
        'errors': len(result.errors),
        'successful': result.wasSuccessful()
    }


def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Review, testing y análisis de cobertura')
    parser.add_argument('--coverage', action='store_true', help='Análisis de cobertura teórica')
    parser.add_argument('--real', action='store_true', help='Análisis de cobertura real')
    parser.add_argument('--all', action='store_true', help='Ejecutar todo')
    
    args = parser.parse_args()
    
    if args.coverage or args.all:
        analyze_theoretical_coverage()
        if not args.all:
            return
    
    if args.real or args.all:
        analyze_real_coverage()
        if not args.all:
            return
    
    # Por defecto, ejecutar tests
    print("=" * 80)
    print("REVISIÓN Y TESTING - CHECKPATCH AUTOFIX")
    print("=" * 80)
    print()
    
    result = run_tests()
    
    print("\n" + "=" * 80)
    print("RESUMEN")
    print("=" * 80)
    print(f"Tests ejecutados: {result['testsRun']}")
    print(f"Fallidos: {result['failures']}")
    print(f"Errores: {result['errors']}")
    print(f"Estado: {'✅ EXITOSO' if result['successful'] else '❌ FALLIDO'}")
    print("=" * 80)
    
    sys.exit(0 if result['successful'] else 1)


if __name__ == '__main__':
    main()
