# constants.py
"""
Constantes y patrones usados en los fixes
"""

import re

# Regex para detectar asignaciones dentro de if/else if
ASSIGNMENT_IN_IF_PATTERN = re.compile(r"\b(if|else\s+if)\s*\((.+)\)\s*$")
COMPOUND_ASSIGN_PATTERN = re.compile(r"\b(\w+\s*(?:[-+*/%&|^]?=|<<=|>>=)\s*[^)&|]+)")
LHS_PATTERN = re.compile(r"(\w+)\s*(?:[-+*/%&|^]?=|<<=|>>=)")

# Patterns para reglas simples (todos los regexes en un solo lugar)
SPACE_AFTER_COMMA = (r",(?=\S)", ", ", True, None)
SPACE_BEFORE_COMMA = (r"\s+,", ",", True, None)
SPACE_BEFORE_PAREN = (" )", ")", False, None)
SPACES_AROUND_EQUALS = (r"(?<![=!<>+\-*/%])\s*=\s*(?![=])", " = ", True, None)
SPACE_AFTER_OPEN_PAREN = (r"\(\s+(?=[^)\s])", "(", True, None)
SPACE_BEFORE_TABS = (" \t", "\t", False, None)
BARE_UNSIGNED = (r"\bunsigned\b(?!\s+int)", "unsigned int", True, None)
SIMPLE_STRTOUL = ("simple_strtoul", "kstrtoul", False, None)
SIMPLE_STRTOL = ("simple_strtol", "kstrtol", False, None)

# Mapeo de constantes para fácil acceso por nombre
PATTERN_MAP = {
	"SPACE_AFTER_COMMA": SPACE_AFTER_COMMA,
	"SPACE_BEFORE_COMMA": SPACE_BEFORE_COMMA,
	"SPACE_BEFORE_PAREN": SPACE_BEFORE_PAREN,
	"SPACES_AROUND_EQUALS": SPACES_AROUND_EQUALS,
	"SPACE_AFTER_OPEN_PAREN": SPACE_AFTER_OPEN_PAREN,
	"SPACE_BEFORE_TABS": SPACE_BEFORE_TABS,
	"BARE_UNSIGNED": BARE_UNSIGNED,
	"SIMPLE_STRTOUL": SIMPLE_STRTOUL,
	"SIMPLE_STRTOL": SIMPLE_STRTOL,
}

# Patrones adicionales usados en fixes más complejos
CHAR_ARRAY_PATTERN = re.compile(r"^\s*char\s+\*\s*\w+\s*\[")
EXTERN_DECL_PATTERN = re.compile(r"\s*extern\s+[\w\s\*\[\]]+\s+\w+(?:\[[^\]]*\])?\s*;")
EXTERN_CAPTURE_PATTERN = re.compile(r"\s*extern\s+[\w\s\*\[\]]+\s+(\w+)(?:\[[^\]]*\])?\s*;")
SYMBOLIC_PERMS_PATTERN = re.compile(r"S_IRUSR\s*\|\s*S_IWUSR")
MSLEEP_PATTERN = re.compile(r"msleep\((\d+)\)")
KMALLOC_PATTERN = re.compile(r"kmalloc\(([^,]+)\)")
MEMCPY_LITERAL_PATTERN = re.compile(r'memcpy\(([^,]+),\s*"([^\"]+)",\s*([^\)]+)\)')
STRNCPY_PATTERN = re.compile(r"strncpy\(([^,]+),\s*([^,]+),\s*([^\)]+)\)")

# Patrones reutilizados en core.py
INDENT_PATTERN = re.compile(r'(\s*)')
EMPTY_RETURN_PATTERN = re.compile(r'^\s*return\s*;\s*$')
BLOCK_COMMENT_END_PATTERN = re.compile(r'^\s*\*/\s*$')
ELSE_IF_PATTERN = re.compile(r'\belse\s+if\b')
IF_PATTERN = re.compile(r'\bif\b')
COMPARISON_OPERATORS = re.compile(r'(!=|==|<=|>=|<|>)')
SIMPLE_VAR_IN_PARENS = re.compile(r'\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)')
FUNCTION_NAME_IN_STRING = re.compile(r'"([a-zA-Z_][a-zA-Z0-9_]+)\s*[:(\s]')
CHAR_ARRAY_DECLARATION = re.compile(r'(^|\s)char\s+(\*+\w+\[\])')
STATIC_CHAR_PTR = re.compile(r'static\s+char\s+\*')
STATIC_CHAR_PTR_DECL = re.compile(r'(static\s+)char\s+(\*+\w+\[\])')
INITDATA_BEFORE = re.compile(r'^(\s*)(static\s+)__initdata\s+(.+?)\s+([^;=]+)(.*);')
INITDATA_AFTER = re.compile(r'^(\s*)(static\s+)(.+?)\s+__initdata\s+([^;=]+)(.*);')
JIFFIES_NOT_EQ = re.compile(r'(\w+)\s*!=\s*jiffies')
JIFFIES_EQ = re.compile(r'(\w+)\s*==\s*jiffies')
STRCPY_PATTERN = re.compile(r'strcpy\s*\(\s*([^,]+),\s*([^)]+)\)')
PRINTK_KERN_CONT = re.compile(r'printk\s*\(\s*KERN_CONT\s*')
STRING_WITH_COMMA = re.compile(r'("[^"]*")\s*,\s*')
STRING_WITH_PAREN = re.compile(r'("[^"]*")\s*\)')

# Mapas reutilizables
ASM_INCLUDE_MAP = {
	"<asm/div64.h>": "<linux/math64.h>",
	"<asm/atomic.h>": "<linux/atomic.h>",
	"<asm/byteorder.h>": "<linux/byteorder.h>",
	"<asm/io.h>": "<linux/io.h>",
	"<asm/cacheflush.h>": "<linux/cacheflush.h>",
}
