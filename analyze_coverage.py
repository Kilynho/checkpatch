"""
Analiza la cobertura de tipos de checkpatch que tenemos implementados
"""

import re
from engine import AUTO_FIX_RULES

# Lista completa de los 227 tipos de checkpatch con su clasificación
# Extraída de: checkpatch.pl --list-types
CHECKPATCH_TYPES = {
    # ERRORS
    'ERROR': [
        'ALLOC_ARRAY_ARGS',
        'ALLOC_SIZEOF_STRUCT',
        'ARCH_DEFINES',
        'ARCH_INCLUDE_LINUX',
        'ASSIGN_IN_IF',
        'AVOID_BUG',
        'BAD_FIXES_TAG',
        'BAD_REPORTED_BY_LINK',
        'BAD_SIGN_OFF',
        'BAD_STABLE_ADDRESS_STYLE',
        'BRACKET_SPACE',
        'C99_COMMENTS',
        'CODE_INDENT',
        'COMMIT_COMMENT_SYMBOL',
        'COMMIT_LOG_LONG_LINE',
        'COMMIT_LOG_USE_LINK',
        'COMMIT_LOG_VERSIONING',
        'COMMIT_LOG_WRONG_LINK',
        'COMMIT_MESSAGE',
        'COMPLEX_MACRO',
        'CONFIG_DESCRIPTION',
        'CONST_CONST',
        'CORRUPTED_PATCH',
        'CVS_KEYWORD',
        'DATE_TIME',
        'DEVICE_ATTR_PERMS',
        'DIFF_IN_COMMIT_MSG',
        'DOS_LINE_ENDINGS',
        'DO_WHILE_MACRO_WITH_TRAILING_SEMICOLON',
        'DT_SCHEMA_BINDING_PATCH',
        'DT_SPLIT_BINDING_PATCH',
        'DUPLICATED_SYSCTL_CONST',
        'ELSE_AFTER_BRACE',
        'EMAIL_SUBJECT',
        'EMBEDDED_FILENAME',
        'ENOSYS',
        'EXECUTE_PERMISSIONS',
        'EXPORTED_WORLD_WRITABLE',
        'FILE_PATH_CHANGES',
        'FROM_SIGN_OFF_MISMATCH',
        'FSF_MAILING_ADDRESS',
        'GERRIT_CHANGE_ID',
        'GIT_COMMIT_ID',
        'HEXADECIMAL_BOOLEAN_TEST',
        'IF_0',
        'INITIALISED_STATIC',
        'INIT_ATTRIBUTE',
        'INVALID_UTF8',
        'KREALLOC_ARG_REUSE',
        'LEADING_SPACE',
        'LINUX_VERSION_CODE',
        'MACRO_ARG_PRECEDENCE',
        'MACRO_ARG_REUSE',
        'MALFORMED_INCLUDE',
        'MISSING_EOF_NEWLINE',
        'MISSING_FIXES_TAG',
        'MISSING_SIGN_OFF',
        'MODIFIED_INCLUDE_ASM',
        'MULTILINE_DEREFERENCE',
        'MULTISTATEMENT_MACRO_USE_DO_WHILE',
        'NEW_TYPEDEFS',
        'NOT_UNIFIED_DIFF',
        'NO_AUTHOR_SIGN_OFF',
        'OPEN_BRACE',
        'OPEN_ENDED_LINE',
        'PATCH_PREFIX',
        'POINTER_LOCATION',
        'QUOTED_WHITESPACE_BEFORE_NEWLINE',
        'RETURN_PARENTHESES',
        'SELF_ASSIGNMENT',
        'SIZEOF_ADDRESS',
        'SPACE_BEFORE_TAB',
        'SPACING',
        'SPDX_LICENSE_TAG',
        'STORAGE_CLASS',
        'SUSPECT_CODE_INDENT',
        'SUSPECT_COMMA_SEMICOLON',
        'SWITCH_CASE_INDENT_LEVEL',
        'TRAILING_SEMICOLON',
        'TRAILING_STATEMENTS',
        'TRAILING_WHITESPACE',
        'UNDOCUMENTED_DT_STRING',
        'UNDOCUMENTED_SETUP',
        'UNKNOWN_COMMIT_ID',
        'UNNECESSARY_PARENTHESES',
        'UNSPECIFIED_INT',
        'UTF8_BEFORE_PATCH',
        'WHILE_AFTER_BRACE',
        'WHITESPACE_AFTER_LINE_CONTINUATION',
    ],
    
    # WARNINGS
    'WARNING': [
        'ALLOC_WITH_MULTIPLY',
        'ARRAY_SIZE',
        'ASSIGNMENT_CONTINUATIONS',
        'AVOID_EXTERNS',
        'AVOID_L_PREFIX',
        'BIT_MACRO',
        'BLOCK_COMMENT_STYLE',
        'BOOL_COMPARISON',
        'BRACES',
        'CAMELCASE',
        'COMPARISON_TO_NULL',
        'CONCATENATED_STRING',
        'CONSIDER_COMPLETION',
        'CONSIDER_KSTRTO',
        'CONSTANT_COMPARISON',
        'CONSTANT_CONVERSION',
        'CONST_READ_MOSTLY',
        'CONST_STRUCT',
        'DATA_RACE',
        'DEEP_INDENTATION',
        'DEFAULT_NO_BREAK',
        'DEFINE_ARCH_HAS',
        'DEPRECATED_API',
        'DEVICE_ATTR_FUNCTIONS',
        'DEVICE_ATTR_RO',
        'DEVICE_ATTR_RW',
        'DEVICE_ATTR_WO',
        'ENOTSUPP',
        'EXPORT_SYMBOL',
        'FLEXIBLE_ARRAY',
        'FUNCTION_ARGUMENTS',
        'FUNCTION_WITHOUT_ARGS',
        'GLOBAL_INITIALISERS',
        'HOTPLUG_SECTION',
        'IF_1',
        'INCLUDE_LINUX',
        'INDENTED_LABEL',
        'INLINE',
        'INLINE_LOCATION',
        'IN_ATOMIC',
        'IS_ENABLED_CONFIG',
        'JIFFIES_COMPARISON',
        'LIKELY_MISUSE',
        'LINE_CONTINUATIONS',
        'LINE_SPACING',
        'LOCKDEP',
        'LOGGING_CONTINUATION',
        'LOGICAL_CONTINUATIONS',
        'LONG_LINE',
        'LONG_LINE_COMMENT',
        'LONG_LINE_STRING',
        'LONG_UDELAY',
        'MACRO_ARG_UNUSED',
        'MACRO_WITH_FLOW_CONTROL',
        'MAINTAINERS_STYLE',
        'MASK_THEN_SHIFT',
        'MEMORY_BARRIER',
        'MEMSET',
        'MINMAX',
        'MISORDERED_TYPE',
        'MISPLACED_INIT',
        'MISSING_SENTINEL',
        'MODULE_LICENSE',
        'MSLEEP',
        'MULTIPLE_ASSIGNMENTS',
        'MULTIPLE_DECLARATION',
        'NAKED_SSCANF',
        'NON_OCTAL_PERMISSIONS',
        'NR_CPUS',
        'OBSOLETE',
        'ONE_SEMICOLON',
        'OOM_MESSAGE',
        'PARENTHESIS_ALIGNMENT',
        'PREFER_DEFINED_ATTRIBUTE_MACRO',
        'PREFER_DEV_LEVEL',
        'PREFER_ETHER_ADDR_COPY',
        'PREFER_ETHER_ADDR_EQUAL',
        'PREFER_ETHTOOL_PUTS',
        'PREFER_ETH_BROADCAST_ADDR',
        'PREFER_ETH_ZERO_ADDR',
        'PREFER_FALLTHROUGH',
        'PREFER_IS_ENABLED',
        'PREFER_KERNEL_TYPES',
        'PREFER_LORE_ARCHIVE',
        'PREFER_PR_LEVEL',
        'PREFER_SEQ_PUTS',
        'PRINTF_0XDECIMAL',
        'PRINTF_L',
        'PRINTF_Z',
        'PRINTK_RATELIMITED',
        'PRINTK_WITHOUT_KERN_LEVEL',
        'REPEATED_WORD',
        'RETURN_VOID',
        'SINGLE_STATEMENT_DO_WHILE_MACRO',
        'SIZEOF_PARENTHESIS',
        'SPLIT_STRING',
        'SSCANF_TO_KSTRTO',
        'STATIC_CONST',
        'STATIC_CONST_CHAR_ARRAY',
        'STRCPY',
        'STRING_FRAGMENTS',
        'STRLCPY',
        'STRNCPY',
        'SYMBOLIC_PERMS',
        'SYSFS_EMIT',
        'TABSTOP',
        'TEST_ATTR',
        'TEST_NOT_ATTR',
        'TEST_NOT_TYPE',
        'TEST_TYPE',
        'TRACE_PRINTK',
        'TRACING_LOGGING',
        'TYPECAST_INT_CONSTANT',
        'TYPO_SPELLING',
        'UAPI_INCLUDE',
        'UNCOMMENTED_DEFINITION',
        'UNCOMMENTED_RGMII_MODE',
        'UNNECESSARY_BREAK',
        'UNNECESSARY_CASTS',
        'UNNECESSARY_ELSE',
        'UNNECESSARY_INT',
        'UNNECESSARY_KERN_LEVEL',
        'UNNECESSARY_MODIFIER',
        'USE_DEVICE_INITCALL',
        'USE_FUNC',
        'USE_LOCKDEP',
        'USE_NEGATIVE_ERRNO',
        'USE_RELATIVE_PATH',
        'USE_SPINLOCK_T',
        'USLEEP_RANGE',
        'VOLATILE',
        'VSPRINTF_POINTER_EXTENSION',
        'VSPRINTF_SPECIFIER_PX',
        'WAITQUEUE_ACTIVE',
        'WEAK_DECLARATION',
        'YIELD',
    ],
    
    # CHECKS (nivel más bajo de severidad)
    'CHECK': []  # Los checks no están en los errores/warnings principales
}

def analyze_coverage():
    """Analiza qué tipos de checkpatch están cubiertos por nuestros fixes"""
    
    # Extraer patrones de mensajes de nuestros fixes
    covered_patterns = set()
    for fix_name, fix_func in AUTO_FIX_RULES.items():
        # Intentar extraer qué tipo de mensaje maneja cada fix
        # basándonos en los nombres de las funciones y sus patrones
        if 'spacing' in fix_name.lower():
            covered_patterns.add('SPACING')
        elif 'return_void' in fix_name.lower():
            covered_patterns.add('RETURN_VOID')
        elif 'initdata' in fix_name.lower():
            covered_patterns.add('MISPLACED_INIT')
        elif 'jiffies' in fix_name.lower():
            covered_patterns.add('JIFFIES_COMPARISON')
        elif 'printk' in fix_name.lower():
            covered_patterns.update(['PRINTK_WITHOUT_KERN_LEVEL', 'PREFER_PR_LEVEL', 'LOGGING_CONTINUATION'])
        elif 'char_array' in fix_name.lower():
            covered_patterns.add('STATIC_CONST_CHAR_ARRAY')
        elif 'func' in fix_name.lower():
            covered_patterns.add('USE_FUNC')
        elif 'line' in fix_name.lower():
            covered_patterns.add('LEADING_SPACE')
    
    # Generar reporte
    print("\n" + "="*80)
    print("ANÁLISIS DE COBERTURA DE CHECKPATCH")
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
            for t in sorted(covered):
                print(f"  - {t}")
        
        if uncovered:
            print(f"\n❌ NO CUBIERTOS ({len(uncovered)}):")
            for t in sorted(uncovered):
                print(f"  - {t}")
    
    # Resumen total
    total_types = len(CHECKPATCH_TYPES['ERROR']) + len(CHECKPATCH_TYPES['WARNING'])
    total_covered = len(covered_patterns)
    total_pct = (total_covered / total_types * 100) if total_types else 0
    
    print("\n" + "="*80)
    print(f"RESUMEN TOTAL: {total_covered}/{total_types} tipos cubiertos ({total_pct:.1f}%)")
    print("="*80)
    
    return {
        'covered': sorted(covered_patterns),
        'total_types': total_types,
        'total_covered': total_covered,
        'coverage_pct': total_pct
    }

if __name__ == "__main__":
    analyze_coverage()