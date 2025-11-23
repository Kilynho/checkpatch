# fixes_core.py
"""
Funciones de autofix complejas
Las funciones simples de reemplazo de patrones están definidas en fix_main.py como tuplas
"""

import re
from fix_utils import apply_line_transform, apply_lines_callback
from fix_constants import (
    ASSIGNMENT_IN_IF_PATTERN,
    COMPOUND_ASSIGN_PATTERN,
    LHS_PATTERN,
    CHAR_ARRAY_PATTERN,
    EXTERN_DECL_PATTERN,
    EXTERN_CAPTURE_PATTERN,
    SYMBOLIC_PERMS_PATTERN,
    MSLEEP_PATTERN,
    KMALLOC_PATTERN,
    MEMCPY_LITERAL_PATTERN,
    STRNCPY_PATTERN,
    ASM_INCLUDE_MAP,
    SPACE_AFTER_COMMA,
    SPACE_BEFORE_COMMA,
    SPACE_BEFORE_PAREN,
    SPACES_AROUND_EQUALS,
    SPACE_AFTER_OPEN_PAREN,
    SPACE_BEFORE_TABS,
    BARE_UNSIGNED,
)

def fix_missing_blank_line(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_missing_blank_line ({file_path}:{line_number})")
    def callback(lines, idx):
        if idx < 0:
            return False
        if idx + 1 < len(lines):
            if lines[idx].strip() != "":
                lines.insert(idx, "\n")
                return True
            else:
                if lines[idx] != "\n":
                    lines[idx] = "\n"
                    return True
                return False
        else:
            lines.append("\n")
            return True

    return apply_lines_callback(file_path, line_number, callback)

def fix_quoted_string_split(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_quoted_string_split ({file_path}:{line_number})")
    def callback(lines, idx):
        target = idx - 1
        if target < 0 or target + 1 >= len(lines):
            return False
        original = lines[target]
        clean = original.rstrip()
        if clean.endswith('"') and not clean.endswith('\\n"'):
            body = clean[:-1].rstrip() + "\\n"
            corrected = body + '"'
            if original.endswith("\n"):
                corrected += "\n"
            lines[target] = corrected
            return True
        return False

    return apply_lines_callback(file_path, line_number, callback)

def fix_assignment_in_if(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_assignment_in_if ({file_path}:{line_number})")
    def callback(lines, idx):
        if idx < 0 or idx >= len(lines):
            return False
        line = lines[idx]

        # detectar if / else if en la línea
        m_else_if = re.search(r"\belse\s+if\b", line)
        m_if = re.search(r"\bif\b", line)
        if m_else_if:
            if_pos = m_else_if.start()
            has_else = True
        elif m_if:
            if_pos = m_if.start()
            has_else = False
        else:
            return False

        # buscar '(' que abre la condición
        paren_open = line.find('(', if_pos)
        if paren_open == -1:
            return False

        # extraer contenido entre paréntesis manejando paréntesis anidados
        i = paren_open
        depth = 0
        end_pos = -1
        while i < len(line):
            if line[i] == '(':
                depth += 1
            elif line[i] == ')':
                depth -= 1
                if depth == 0:
                    end_pos = i
                    break
            i += 1
        if end_pos == -1:
            return False

        expr = line[paren_open+1:end_pos].strip()

        # helper: limpiar paréntesis envolventes redundantes
        def strip_outer_parens(s):
            s = s.strip()
            while s.startswith('(') and s.endswith(')'):
                inner = s[1:-1]
                depth = 0
                balanced = True
                for ch in inner:
                    if ch == '(':
                        depth += 1
                    elif ch == ')':
                        depth -= 1
                        if depth < 0:
                            balanced = False
                            break
                if not balanced or depth != 0:
                    break
                s = inner.strip()
            return s

        expr_clean = strip_outer_parens(expr)

        # buscar asignación dentro de la expresión ya limpia
        # Primero encontrar la posición del primer operador de comparación
        comp_pattern = re.compile(r'(!=|==|<=|>=|<|>)')
        m_comp = comp_pattern.search(expr_clean)
        
        if m_comp:
            comp_pos = m_comp.start()
            expr_with_assign = expr_clean[:comp_pos].rstrip()
        else:
            expr_with_assign = expr_clean
        
        # Ahora encontrar la asignación
        assign_pattern = re.compile(r"([A-Za-z_][A-Za-z0-9_\->\[\]\.]*)\s*((?:\+=|-=|\*=|/=|%=|&=|\|=|\^=|=))\s*(.*)")
        m_assign = assign_pattern.search(expr_with_assign)
        
        if not m_assign:
            return False

        var = m_assign.group(1)
        op = m_assign.group(2)  # el operador de asignación
        value_part = m_assign.group(3).rstrip()
        
        # Remove trailing unmatched parentheses (excess closing parens)
        open_count = value_part.count('(')
        close_count = value_part.count(')')
        if close_count > open_count:
            excess = close_count - open_count
            value_part = value_part[:-excess]
        
        assignment = f"{var} {op} {value_part}"

        # limpiar paréntesis envolventes en la asignación antes de insertar
        assignment_clean = strip_outer_parens(assignment)

        # obtener nombre de variable izquierdo
        lhs = LHS_PATTERN.match(assignment)
        if not lhs:
            return False
        var_name = lhs.group(1)
        if not var_name:
            return False

        # construir condición: reemplazar la asignación por el nombre de variable en expr_clean
        # expr_clean ya tiene los paréntesis externos eliminados
        # buscar la asignación dentro de expr_clean y reemplazarla por la variable
        assignment_idx = expr_clean.find(assignment)
        if assignment_idx >= 0:
            # reemplazar la asignación por la variable
            cond = (expr_clean[:assignment_idx] + var_name + expr_clean[assignment_idx + len(assignment):]).strip()
        else:
            cond = var_name
        
        # limpiar paréntesis externos de la condición resultante
        cond = strip_outer_parens(cond)
        
        # limpiar paréntesis alrededor de variables simples: (variable) -> variable
        cond = re.sub(r'\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)', r'\1', cond)

        base_indent = re.match(r"(\s*)", line).group(1)
        trailing = line[end_pos+1:].rstrip('\n')

        # Si es 'else if' con llave de apertura en la misma línea, hacer transformación especial
        if has_else and '{' in trailing:
            # Estructura: } else if ((asignación) comparación) {
            # Objetivo: } else {
            #               asignación;
            #               if (condición) {
            
            # Extraer el prefix antes de 'else' (debería ser '}' + espacios)
            prefix_before_else = line[:if_pos]
            
            # Nueva línea 1: } else {
            new_first = prefix_before_else.rstrip() + ' else {\n'
            
            # Indentación interna (aumentar 4 espacios si ya usa espacios, o 1 tab si usa tabs)
            if '\t' in base_indent:
                inner_indent = base_indent + '\t'
            else:
                inner_indent = base_indent + '    '
            
            # Nueva línea 2: asignación;
            inner_assign = inner_indent + assignment_clean + ';\n'
            
            # Nueva línea 3: if (condición) {
            inner_if = inner_indent + 'if (' + cond + ') {\n'
            
            # Reemplazar la línea actual por las tres nuevas
            insert = [new_first, inner_assign, inner_if]
            lines[idx:idx+1] = insert
            
            # Encontrar la llave de cierre correspondiente del bloque original
            # y re-indentarizar todo el contenido del bloque original
            scan_i = idx + len(insert)
            depth = 1
            body_start = scan_i
            
            # Calcular indentación original del cuerpo (basándose en la primera línea del cuerpo)
            original_body_indent = None
            for k in range(body_start, len(lines)):
                line_content = lines[k].lstrip()
                if line_content.strip():  # Primera línea no vacía
                    indent_len = len(lines[k]) - len(line_content)
                    original_body_indent = lines[k][:indent_len]
                    break
            
            if original_body_indent is None:
                original_body_indent = base_indent + '    '
            
            # Indentación nueva para el cuerpo: inner_indent + 4 espacios (o 1 tab si ya usa tabs)
            if '\t' in inner_indent:
                new_body_indent = inner_indent + '\t'
            else:
                new_body_indent = inner_indent + '    '
            
            indent_delta = len(new_body_indent) - len(original_body_indent)
            
            for j in range(scan_i, len(lines)):
                line_j = lines[j]
                pos_in_line = 0
                for pos_in_line, ch in enumerate(line_j):
                    if ch == '{':
                        depth += 1
                    elif ch == '}':
                        depth -= 1
                        if depth == 0:
                            # Encontramos la llave de cierre a pos_in_line en línea j
                            # Re-indentarizar todas las líneas del cuerpo
                            if indent_delta != 0:
                                for k in range(body_start, j):
                                    if lines[k].strip():  # Solo si no está vacía
                                        lines[k] = new_body_indent + lines[k][len(original_body_indent):]
                            
                            # Ahora extraer el resto de la línea después de la '}'
                            before_close = line_j[:pos_in_line]
                            after_close = line_j[pos_in_line+1:].lstrip()
                            
                            # Insertar llave de cierre para el if
                            lines.insert(j, inner_indent + '}\n')
                            
                            # Modificar línea j+1 (el cierre del else)
                            # Si hay contenido después (ej: else if), incluirlo en la misma línea
                            if after_close.strip():
                                lines[j+1] = base_indent + '} ' + after_close
                            else:
                                lines[j+1] = base_indent + '}\n'
                            
                            return True
            return False

        # preparar nuevas líneas: asignación; then if (cond) <trailing>
        assign_line = f"{base_indent}{assignment_clean};\n"
        if_line = f"{base_indent}{'else ' if has_else else ''}if ({cond}){trailing if trailing else ''}\n"

        # Caso general: reemplazar la línea actual por asignación + if
        lines[idx:idx+1] = [assign_line, if_line]
        return True

    return apply_lines_callback(file_path, line_number, callback)

def fix_switch_case_indent(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_switch_case_indent ({file_path}:{line_number})")
    def callback(lines, idx):
        if idx < 0 or idx >= len(lines):
            return False
        stripped = lines[idx].lstrip()
        if not stripped.startswith("switch"):
            return False
        switch_indent = lines[idx][:len(lines[idx]) - len(stripped)]
        updated = False
        depth = 0
        i = idx
        while i < len(lines):
            line = lines[i]
            stripped = line.lstrip()
            depth += line.count("{")
            depth -= line.count("}")
            if i > idx and depth == 0:
                break
            if depth == 1 and (stripped.startswith("case ") or stripped.startswith("default")):
                new_line = switch_indent + stripped
                if new_line != line:
                    lines[i] = new_line
                    updated = True
            i += 1
        return updated

    return apply_lines_callback(file_path, line_number, callback)

def fix_indent_tabs(file_path, line_number):
    def transform(line):
        stripped = line.lstrip('\t ')
        indent = line[:len(line) - len(stripped)]
        col = 0
        for ch in indent:
            if ch == "\t":
                col = (col // 8 + 1) * 8
            else:
                col += 1
        needed_tabs = col // 8
        new_indent = "\t" * needed_tabs
        new_line = new_indent + stripped
        return new_line if new_line != line else None
    return apply_line_transform(file_path, line_number, transform)

def fix_trailing_whitespace(file_path, line_number):
    def transform(line):
        return line.rstrip() + "\n"
    return apply_line_transform(file_path, line_number, transform)

def fix_initconst(file_path, line_number):
    def transform(line):
        if "const" in line and "__initdata" in line:
            return line.replace("__initdata", "__initconst", 1)
        return None
    return apply_line_transform(file_path, line_number, transform)

def fix_prefer_notice(file_path, line_number):
    def transform(line):
        if "printk(KERN_NOTICE" in line:
            return line.replace("printk(KERN_NOTICE ", "pr_notice(", 1)
        return None
    return apply_line_transform(file_path, line_number, transform)

def fix_void_return(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_void_return ({file_path}:{line_number})")
    def transform(line):
        if line.strip() == "return;":
            return ""
        return None
    return apply_line_transform(file_path, line_number, transform)

def fix_unnecessary_braces(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_unnecessary_braces ({file_path}:{line_number})")
    def callback(lines, idx):
        if idx < 1 or idx+1 >= len(lines):
            return False
        if lines[idx].strip() != "{":
            return False
        if idx+2 >= len(lines) or lines[idx+2].strip() != "}":
            return False
        del lines[idx+2]
        del lines[idx]
        return True

    return apply_lines_callback(file_path, line_number, callback)

def fix_block_comment_trailing(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_block_comment_trailing ({file_path}:{line_number})")
    def callback(lines, idx):
        if idx < 0 or idx >= len(lines):
            return False
        line = lines[idx]
        if "*/" in line and not line.strip().endswith("*/"):
            new_line = line.replace("*/", "").rstrip()
            lines[idx] = new_line
            lines.insert(idx + 1, " */\n")
            return True
        return False

    return apply_lines_callback(file_path, line_number, callback)

def fix_char_array_static_const(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_char_array_static_const ({file_path}:{line_number})")
    def transform(line):
        if CHAR_ARRAY_PATTERN.search(line) and "static" not in line:
            return line.replace("char", "static const char", 1)
        return None
    return apply_line_transform(file_path, line_number, transform)

def fix_spdx_comment(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_spdx_comment ({file_path}:{line_number})")
    def transform(line):
        if line.strip().startswith("// SPDX-"):
            return "/* " + line.strip()[3:] + " */\n"
        return None
    return apply_line_transform(file_path, line_number, transform)

def fix_extern_in_c(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_extern_in_c ({file_path}:{line_number})")
    def callback(lines, idx):
        if idx < 0 or idx >= len(lines):
            return False
        line = lines[idx]
        if not EXTERN_DECL_PATTERN.match(line):
            return False
        m = EXTERN_CAPTURE_PATTERN.match(line)
        if m:
            varname = m.group(1)
            for j, l in enumerate(lines):
                if j != idx and re.search(rf"\b{re.escape(varname)}\b", l):
                    return False
        lines[idx] = "// " + line
        return True

    return apply_lines_callback(file_path, line_number, callback)

def fix_symbolic_permissions(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_symbolic_permissions ({file_path}:{line_number})")
    def transform(line):
        if "S_IRUSR" in line and "S_IWUSR" in line:
            return SYMBOLIC_PERMS_PATTERN.sub("0600", line)
        return None
    return apply_line_transform(file_path, line_number, transform)

def fix_printk_info(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_printk_info ({file_path}:{line_number})")
    def transform(line):
        if "printk(KERN_INFO" in line:
            new_line = line.replace("printk(KERN_INFO", "pr_info")
            return new_line
        return None
    return apply_line_transform(file_path, line_number, transform)

def fix_printk_err(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_printk_err ({file_path}:{line_number})")
    def transform(line):
        if "printk(KERN_ERR" in line:
            return line.replace("printk(KERN_ERR", "pr_err")
        return None
    return apply_line_transform(file_path, line_number, transform)

def fix_printk_warn(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_printk_warn ({file_path}:{line_number})")
    def transform(line):
        if "printk(KERN_WARNING" in line:
            return line.replace("printk(KERN_WARNING", "pr_warn")
        return None
    return apply_line_transform(file_path, line_number, transform)

def fix_printk_debug(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_printk_debug ({file_path}:{line_number})")
    def transform(line):
        if "printk(KERN_DEBUG" in line:
            return line.replace("printk(KERN_DEBUG", "pr_debug")
        return None
    return apply_line_transform(file_path, line_number, transform)

def fix_asm_includes(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_asm_includes ({file_path}:{line_number})")
    mapping = ASM_INCLUDE_MAP
    def transform(line):
        new = line
        for asm_inc, linux_inc in mapping.items():
            if asm_inc in new:
                new = new.replace(asm_inc, linux_inc)
        return new if new != line else None
    return apply_line_transform(file_path, line_number, transform)

def fix_msleep_too_small(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_msleep_too_small ({file_path}:{line_number})")
    def transform(line):
        m = MSLEEP_PATTERN.search(line)
        if not m:
            return None
        value = int(m.group(1))
        if value >= 20:
            return None
        us = value * 1000
        return f"usleep_range({us}, {us + 1000});\n"
    return apply_line_transform(file_path, line_number, transform)

def fix_kmalloc_no_flag(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_kmalloc_no_flag ({file_path}:{line_number})")
    def transform(line):
        m = KMALLOC_PATTERN.search(line)
        if not m:
            return None
        return line.replace(m.group(0), f"kmalloc({m.group(1)}, GFP_KERNEL)")
    return apply_line_transform(file_path, line_number, transform)

def fix_memcpy_literal(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_memcpy_literal ({file_path}:{line_number})")
    def transform(line):
        m = MEMCPY_LITERAL_PATTERN.search(line)
        if not m:
            return None
        dest, literal, size = m.groups()
        return f"strscpy({dest.strip()}, \"{literal}\", {size.strip()});\n"
    return apply_line_transform(file_path, line_number, transform)

def fix_of_read_no_check(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_of_read_no_check ({file_path}:{line_number})")
    def transform(line):
        if "of_property_read_u32" not in line:
            return None
        indent = " " * (len(line) - len(line.lstrip()))
        stripped = line.strip()
        new_code = (
            f"{indent}if ({stripped})\n"
            f"{indent}    return -EINVAL;\n"
        )
        return new_code
    return apply_line_transform(file_path, line_number, transform)

def fix_strncpy(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_strncpy ({file_path}:{line_number})")
    def transform(line):
        m = STRNCPY_PATTERN.search(line)
        if not m:
            return None
        dest, src, size = m.groups()
        return f"strscpy({dest.strip()}, {src.strip()}, {size.strip()});\n"
    return apply_line_transform(file_path, line_number, transform)


def fix_missing_blank_line(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_missing_blank_line ({file_path}:{line_number})")
    def callback(lines, idx):
        if idx < 0:
            return False
        if idx + 1 < len(lines):
            if lines[idx].strip() != "":
                lines.insert(idx, "\n")
                return True
            else:
                if lines[idx] != "\n":
                    lines[idx] = "\n"
                    return True
                return False
        else:
            lines.append("\n")
            return True

    return apply_lines_callback(file_path, line_number, callback)

def fix_quoted_string_split(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_quoted_string_split ({file_path}:{line_number})")
    def callback(lines, idx):
        # original implementation operated on line_number - 2
        target = idx - 1
        if target < 0 or target + 1 >= len(lines):
            return False
        original = lines[target]
        clean = original.rstrip()
        if clean.endswith('"') and not clean.endswith('\\n"'):
            body = clean[:-1].rstrip() + "\\n"
            corrected = body + '"'
            if original.endswith("\n"):
                corrected += "\n"
            lines[target] = corrected
            return True
        return False

    return apply_lines_callback(file_path, line_number, callback)



def fix_trailing_whitespace(file_path, line_number):
    def transform(line):
        return line.rstrip() + "\n"
    return apply_line_transform(file_path, line_number, transform)

def fix_switch_case_indent(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_switch_case_indent ({file_path}:{line_number})")
    def callback(lines, idx):
        if idx < 0 or idx >= len(lines):
            return False
        stripped = lines[idx].lstrip()
        if not stripped.startswith("switch"):
            return False
        switch_indent = lines[idx][:len(lines[idx]) - len(stripped)]
        updated = False
        depth = 0
        i = idx
        while i < len(lines):
            line = lines[i]
            stripped = line.lstrip()
            depth += line.count("{")
            depth -= line.count("}")
            if i > idx and depth == 0:
                break
            if depth == 1 and (stripped.startswith("case ") or stripped.startswith("default")):
                new_line = switch_indent + stripped
                if new_line != line:
                    lines[i] = new_line
                    updated = True
            i += 1
        return updated

    return apply_lines_callback(file_path, line_number, callback)

def fix_indent_tabs(file_path, line_number):
    def transform(line):
        stripped = line.lstrip('\t ')
        indent = line[:len(line) - len(stripped)]
        col = 0
        for ch in indent:
            if ch == "\t":
                col = (col // 8 + 1) * 8
            else:
                col += 1
        needed_tabs = col // 8
        new_indent = "\t" * needed_tabs
        new_line = new_indent + stripped
        return new_line if new_line != line else None
    return apply_line_transform(file_path, line_number, transform)

def fix_initconst(file_path, line_number):
    def transform(line):
        if "const" in line and "__initdata" in line:
            return line.replace("__initdata", "__initconst", 1)
        return None
    return apply_line_transform(file_path, line_number, transform)

def fix_prefer_notice(file_path, line_number):
    def transform(line):
        if "printk(KERN_NOTICE" in line:
            return line.replace("printk(KERN_NOTICE ", "pr_notice(", 1)
        return None
    return apply_line_transform(file_path, line_number, transform)

def fix_space_after_open_paren(file_path, line_number):
    # moved to tuple-based rule in fix_constants.py / fix_main.py
    return False

def fix_space_before_tabs(file_path, line_number):
    # handled by tuple-based rule in fix_constants.py / fix_main.py
    return False

def fix_void_return(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_void_return ({file_path}:{line_number})")
    def transform(line):
        if line.strip() == "return;":
            return ""
        return None
    return apply_line_transform(file_path, line_number, transform)

def fix_unnecessary_braces(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_unnecessary_braces ({file_path}:{line_number})")
    def callback(lines, idx):
        if idx < 1 or idx+1 >= len(lines):
            return False
        # Debe ser: '{' en esta línea
        if lines[idx].strip() != "{":
            return False
        # Y la siguiente NO debe ser un bloque grande
        if idx+2 >= len(lines) or lines[idx+2].strip() != "}":
            return False
        # Elimino llaves
        del lines[idx+2]
        del lines[idx]
        return True

    return apply_lines_callback(file_path, line_number, callback)

def fix_block_comment_trailing(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_block_comment_trailing ({file_path}:{line_number})")
    def callback(lines, idx):
        if idx < 0 or idx >= len(lines):
            return False
        line = lines[idx]
        if "*/" in line and not line.strip().endswith("*/"):
            new_line = line.replace("*/", "").rstrip()
            lines[idx] = new_line
            lines.insert(idx + 1, " */\n")
            return True
        return False

    return apply_lines_callback(file_path, line_number, callback)

def fix_char_array_static_const(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_char_array_static_const ({file_path}:{line_number})")
    def transform(line):
        # Caso: char *foo[] = { ... };
        if CHAR_ARRAY_PATTERN.search(line) and "static" not in line:
            return line.replace("char", "static const char", 1)
        return None
    return apply_line_transform(file_path, line_number, transform)

def fix_bare_unsigned(file_path, line_number):
    # handled by tuple-based rule in fix_constants.py / fix_main.py
    return False

def fix_spdx_comment(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_spdx_comment ({file_path}:{line_number})")
    def transform(line):
        if line.strip().startswith("// SPDX-"):
            return "/* " + line.strip()[3:] + " */\n"
        return None
    return apply_line_transform(file_path, line_number, transform)

def fix_extern_in_c(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_extern_in_c ({file_path}:{line_number})")
    def callback(lines, idx):
        if idx < 0 or idx >= len(lines):
            return False
        line = lines[idx]
        # Detect extern statement
        if not EXTERN_DECL_PATTERN.match(line):
            return False
        # Extract variable name using a safer regex capture
        m = EXTERN_CAPTURE_PATTERN.match(line)
        if m:
            varname = m.group(1)
            # Search for usage excluding the extern itself
            for j, l in enumerate(lines):
                if j != idx and re.search(rf"\b{re.escape(varname)}\b", l):
                    # Variable is used → don't comment automatically
                    return False
        # Safe: variable is not used → comment it out
        lines[idx] = "// " + line
        return True

    return apply_lines_callback(file_path, line_number, callback)

def fix_simple_strtoul(file_path, line_number):
    # replaced by SIMPLE_STRTOUL tuple rule in fix_constants.py / fix_main.py
    return False

def fix_simple_strtol(file_path, line_number):
    # replaced by SIMPLE_STRTOL tuple rule in fix_constants.py / fix_main.py
    return False

def fix_symbolic_permissions(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_symbolic_permissions ({file_path}:{line_number})")
    def transform(line):
        if "S_IRUSR" in line and "S_IWUSR" in line:
            return SYMBOLIC_PERMS_PATTERN.sub("0600", line)
        return None
    return apply_line_transform(file_path, line_number, transform)

def fix_printk_info(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_printk_info ({file_path}:{line_number})")
    def transform(line):
        if "printk(KERN_INFO" in line:
            new_line = line.replace("printk(KERN_INFO", "pr_info")
            new_line = new_line.replace(")", ")")  # mantener estilo
            return new_line
        return None
    return apply_line_transform(file_path, line_number, transform)

def fix_printk_err(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_printk_err ({file_path}:{line_number})")
    def transform(line):
        if "printk(KERN_ERR" in line:
            return line.replace("printk(KERN_ERR", "pr_err")
        return None
    return apply_line_transform(file_path, line_number, transform)

def fix_printk_warn(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_printk_warn ({file_path}:{line_number})")
    def transform(line):
        if "printk(KERN_WARNING" in line:
            return line.replace("printk(KERN_WARNING", "pr_warn")
        return None
    return apply_line_transform(file_path, line_number, transform)

def fix_printk_debug(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_printk_debug ({file_path}:{line_number})")
    def transform(line):
        if "printk(KERN_DEBUG" in line:
            return line.replace("printk(KERN_DEBUG", "pr_debug")
        return None
    return apply_line_transform(file_path, line_number, transform)

def fix_asm_includes(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_asm_includes ({file_path}:{line_number})")
    mapping = {
        "<asm/div64.h>": "<linux/math64.h>",
        "<asm/atomic.h>": "<linux/atomic.h>",
        "<asm/byteorder.h>": "<linux/byteorder.h>",
    }
    def transform(line):
        new = line
        for asm_inc, linux_inc in mapping.items():
            if asm_inc in new:
                new = new.replace(asm_inc, linux_inc)
        return new if new != line else None
    return apply_line_transform(file_path, line_number, transform)

def fix_msleep_too_small(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_msleep_too_small ({file_path}:{line_number})")
    def transform(line):
        m = MSLEEP_PATTERN.search(line)
        if not m:
            return None
        value = int(m.group(1))
        if value >= 20:
            return None
        us = value * 1000
        return f"usleep_range({us}, {us + 1000});\n"
    return apply_line_transform(file_path, line_number, transform)

def fix_kmalloc_no_flag(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_kmalloc_no_flag ({file_path}:{line_number})")
    def transform(line):
        m = KMALLOC_PATTERN.search(line)
        if not m:
            return None
        return line.replace(m.group(0), f"kmalloc({m.group(1)}, GFP_KERNEL)")
    return apply_line_transform(file_path, line_number, transform)

def fix_memcpy_literal(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_memcpy_literal ({file_path}:{line_number})")
    def transform(line):
        m = MEMCPY_LITERAL_PATTERN.search(line)
        if not m:
            return None
        dest, literal, size = m.groups()
        return f"strscpy({dest.strip()}, \"{literal}\", {size.strip()});\n"
    return apply_line_transform(file_path, line_number, transform)

def fix_of_read_no_check(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_of_read_no_check ({file_path}:{line_number})")
    def transform(line):
        if "of_property_read_u32" not in line:
            return None
        indent = " " * (len(line) - len(line.lstrip()))
        stripped = line.strip()
        new_code = (
            f"{indent}if ({stripped})\n"
            f"{indent}    return -EINVAL;\n"
        )
        return new_code
    return apply_line_transform(file_path, line_number, transform)

def fix_strncpy(file_path, line_number):
    print(f"[DEBUG] Entrando en fix_strncpy ({file_path}:{line_number})")
    def transform(line):
        m = STRNCPY_PATTERN.search(line)
        if not m:
            return None
        dest, src, size = m.groups()
        return f"strscpy({dest.strip()}, {src.strip()}, {size.strip()});\n"
    return apply_line_transform(file_path, line_number, transform)
