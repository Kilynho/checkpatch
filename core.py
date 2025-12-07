# core.py
"""
Funciones de autofix complejas
Las funciones simples de reemplazo de patrones están definidas en engine.py como tuplas
"""

import re
from utils import apply_line_transform, apply_lines_callback
from constants import (
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
    INDENT_PATTERN,
    EMPTY_RETURN_PATTERN,
    BLOCK_COMMENT_END_PATTERN,
    ELSE_IF_PATTERN,
    IF_PATTERN,
    COMPARISON_OPERATORS,
    SIMPLE_VAR_IN_PARENS,
    FUNCTION_NAME_IN_STRING,
    CHAR_ARRAY_DECLARATION,
    STATIC_CHAR_PTR,
    STATIC_CHAR_PTR_DECL,
    INITDATA_BEFORE,
    INITDATA_AFTER,
    JIFFIES_NOT_EQ,
    JIFFIES_EQ,
    STRCPY_PATTERN,
    PRINTK_KERN_CONT,
    STRING_WITH_COMMA,
    STRING_WITH_PAREN,
)

def fix_missing_blank_line(file_path, line_number):
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
    def callback(lines, idx):
        if idx < 0 or idx >= len(lines):
            return False
        line = lines[idx]

        # detectar if / else if en la línea
        m_else_if = ELSE_IF_PATTERN.search(line)
        m_if = IF_PATTERN.search(line)
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
        m_comp = COMPARISON_OPERATORS.search(expr_clean)
        
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
        cond = SIMPLE_VAR_IN_PARENS.sub(r'\1', cond)

        base_indent = INDENT_PATTERN.match(line).group(1)
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
    def callback(lines, idx):
        line = lines[idx]
        if "printk(KERN_NOTICE " in line and '"' in line:
            lines[idx] = line.replace("printk(KERN_NOTICE ", "pr_notice(", 1)
            return True
        elif "printk(KERN_NOTICE" in line and '"' not in line:
            if idx + 1 < len(lines):
                next_line = lines[idx + 1]
                indent = INDENT_PATTERN.match(line).group(1)
                lines[idx] = indent + "pr_notice(" + next_line.strip()
                del lines[idx + 1]
                return True
        return False
    return apply_lines_callback(file_path, line_number, callback)

def fix_void_return(file_path, line_number):
    def callback(lines, idx):
        # Checkpatch reporta la línea después del return (la llave de cierre)
        # Buscar el return; en la línea anterior
        if idx > 0 and EMPTY_RETURN_PATTERN.match(lines[idx - 1]):
            del lines[idx - 1]
            return True
        # Por si acaso, también verificar línea actual
        if EMPTY_RETURN_PATTERN.match(lines[idx]):
            del lines[idx]
            return True
        return False
    return apply_lines_callback(file_path, line_number, callback)

def fix_unnecessary_braces(file_path, line_number):
    def callback(lines, idx):
        # Checkpatch reports on the if/for/while line
        # Look for opening brace on same line or next line
        line = lines[idx]
        if line.rstrip().endswith('{'):
            # Brace at end of current line: "if (x) {"
            # Find the single statement (idx+1) and closing brace (idx+2)
            if idx + 2 >= len(lines):
                return False
            if lines[idx + 2].strip() != '}':
                return False
            # Remove braces: change "if (x) {" to "if (x)"
            lines[idx] = line.rstrip()[:-1].rstrip() + '\n'
            del lines[idx + 2]  # Remove }
            return True
        elif idx + 1 < len(lines) and lines[idx + 1].strip() == '{':
            # Brace on next line alone
            if idx + 3 >= len(lines):
                return False
            if lines[idx + 3].strip() != '}':
                return False
            # Remove lines with braces
            del lines[idx + 3]  # Remove }
            del lines[idx + 1]  # Remove {
            return True
        return False

    return apply_lines_callback(file_path, line_number, callback)

def fix_block_comment_trailing(file_path, line_number):
    def callback(lines, idx):
        line = lines[idx]
        if line.rstrip().endswith('*/') and not BLOCK_COMMENT_END_PATTERN.match(line):
            content = line.rstrip()[:-2].rstrip()
            indent = INDENT_PATTERN.match(line).group(1)
            lines[idx] = content + '\n'
            lines.insert(idx + 1, indent + ' */')
            return True
        return False
    return apply_lines_callback(file_path, line_number, callback)

def fix_char_array_static_const(file_path, line_number):
    def transform(line):
        # Patrón: static char *nombre[] o static char **nombre o char *nombre[]
        # Debe convertirse a: static const char * const nombre[]
        
        # Caso 1: static char *nombre[] o static char **nombre
        match = STATIC_CHAR_PTR_DECL.search(line)
        if match:
            return line.replace(match.group(0), f'{match.group(1)}const char * const {match.group(2)[1:]}', 1)
        
        # Caso 2: char *nombre[] sin static (agregar static const)
        match = re.search(r'(^|\s)char\s+(\*+\w+\[\])', line)
        if match and 'static' not in line:
            return line.replace(match.group(0), f'{match.group(1)}static const char * const {match.group(2)[1:]}', 1)
        
        # Caso 3: ya está static char pero le falta const al final del *
        # static char *nombre[] → static const char * const nombre[]
        if STATIC_CHAR_PTR.search(line) and 'const char' not in line:
            return line.replace('static char *', 'static const char * const ', 1)
        
        return None
    return apply_line_transform(file_path, line_number, transform)

def fix_spdx_comment(file_path, line_number):
    def transform(line):
        if line.strip().startswith("// SPDX-"):
            return "/* " + line.strip()[3:] + " */\n"
        return None
    return apply_line_transform(file_path, line_number, transform)

def fix_extern_in_c(file_path, line_number):
    def callback(lines, idx):
        line = lines[idx]
        if "extern" in line:
            del lines[idx]
            return True
        return False
    return apply_lines_callback(file_path, line_number, callback)

def fix_symbolic_permissions(file_path, line_number):
    def transform(line):
        if "S_IRUSR" in line and "S_IWUSR" in line:
            return SYMBOLIC_PERMS_PATTERN.sub("0600", line)
        return None
    return apply_line_transform(file_path, line_number, transform)

def fix_printk_info(file_path, line_number):
    def callback(lines, idx):
        line = lines[idx]
        # Caso 1: Todo en una línea
        if "printk(KERN_INFO " in line and '"' in line:
            lines[idx] = line.replace("printk(KERN_INFO ", "pr_info(", 1)
            return True
        # Caso 2: Multilínea - KERN_INFO en línea anterior
        if idx > 0 and "printk(KERN_INFO" in lines[idx - 1] and '"' in line:
            indent = re.match(r'(\s*)', lines[idx - 1]).group(1)
            lines[idx] = indent + "pr_info(" + line.strip()
            del lines[idx - 1]
            return True
        # Caso 3: Formato multilínea - printk(KERN_INFO en línea actual, mensaje en siguiente
        if "printk(KERN_INFO" in line and '"' not in line and idx + 1 < len(lines) and '"' in lines[idx + 1]:
            indent = INDENT_PATTERN.match(line).group(1)
            lines[idx] = indent + "pr_info(" + lines[idx + 1].strip()
            del lines[idx + 1]
            return True
        return False
    return apply_lines_callback(file_path, line_number, callback)

def fix_printk_err(file_path, line_number):
    def callback(lines, idx):
        line = lines[idx]
        # Caso 1: Todo en una línea
        if "printk(KERN_ERR " in line and '"' in line:
            lines[idx] = line.replace("printk(KERN_ERR ", "pr_err(", 1)
            return True
        # Caso 2: Multilínea - KERN_ERR en línea anterior
        if idx > 0 and "printk(KERN_ERR" in lines[idx - 1] and '"' in line:
            # Combinar: quitar la línea anterior y poner pr_err en la actual
            indent = re.match(r'(\s*)', lines[idx - 1]).group(1)
            lines[idx] = indent + "pr_err(" + line.strip()
            del lines[idx - 1]
            return True
        return False
    return apply_lines_callback(file_path, line_number, callback)

def fix_printk_warn(file_path, line_number):
    def callback(lines, idx):
        line = lines[idx]
        if "printk(KERN_WARNING " in line and '"' in line:
            lines[idx] = line.replace("printk(KERN_WARNING ", "pr_warn(", 1)
            return True
        if idx > 0 and "printk(KERN_WARNING" in lines[idx - 1] and '"' in line:
            indent = re.match(r'(\s*)', lines[idx - 1]).group(1)
            lines[idx] = indent + "pr_warn(" + line.strip()
            del lines[idx - 1]
            return True
        return False
    return apply_lines_callback(file_path, line_number, callback)

def fix_printk_debug(file_path, line_number):
    def callback(lines, idx):
        line = lines[idx]
        if "printk(KERN_DEBUG " in line and '"' in line:
            lines[idx] = line.replace("printk(KERN_DEBUG ", "pr_debug(", 1)
            return True
        if idx > 0 and "printk(KERN_DEBUG" in lines[idx - 1] and '"' in line:
            indent = re.match(r'(\s*)', lines[idx - 1]).group(1)
            lines[idx] = indent + "pr_debug(" + line.strip()
            del lines[idx - 1]
            return True
        return False
    return apply_lines_callback(file_path, line_number, callback)

def fix_printk_emerg(file_path, line_number):
    def callback(lines, idx):
        line = lines[idx]
        # Caso 1: Todo en una línea
        if "printk(KERN_EMERG " in line and '"' in line:
            lines[idx] = line.replace("printk(KERN_EMERG ", "pr_emerg(", 1)
            return True
        # Caso 2: Multilínea - KERN_EMERG en línea anterior
        if idx > 0 and "printk(KERN_EMERG" in lines[idx - 1] and '"' in line:
            indent = re.match(r'(\s*)', lines[idx - 1]).group(1)
            lines[idx] = indent + "pr_emerg(" + line.strip()
            del lines[idx - 1]
            return True
        # Caso 3: Formato multilínea - printk(KERN_EMERG en línea actual, mensaje en siguiente
        if "printk(KERN_EMERG" in line and '"' not in line and idx + 1 < len(lines) and '"' in lines[idx + 1]:
            indent = INDENT_PATTERN.match(line).group(1)
            lines[idx] = indent + "pr_emerg(" + lines[idx + 1].strip()
            del lines[idx + 1]
            return True
        return False
    return apply_lines_callback(file_path, line_number, callback)

def fix_printk_kern_level(file_path, line_number):
    def transform(line):
        # Detectar printk sin KERN_* level
        if 'printk(' in line and 'KERN_' not in line:
            # Si termina con \n"), probablemente sea continuación
            if line.rstrip().endswith('\\n")') or line.rstrip().endswith('\\n");'):
                # Añadir KERN_INFO después de printk(
                return line.replace('printk("', 'printk(KERN_INFO "', 1)
            # Si no tiene comillas en la misma línea, puede ser multilínea
            elif '"' not in line and 'printk(' in line:
                return line.replace('printk(', 'printk(KERN_INFO ', 1)
            # Caso de continuación (sin \n al final del string)
            else:
                # Probablemente sea KERN_CONT
                return line.replace('printk("', 'printk(KERN_CONT "', 1)
        return None
    return apply_line_transform(file_path, line_number, transform)

def fix_jiffies_comparison(file_path, line_number):
    def transform(line):
        # Detectar comparaciones directas de jiffies
        # Reemplazar: jiffies != X -> time_after(jiffies, X)
        if 'jiffies !=' in line or '!= jiffies' in line:
            # Capturar la comparación
            match = JIFFIES_NOT_EQ.search(line)
            if match:
                var = match.group(1)
                return line.replace(f'{var} != jiffies', f'time_after(jiffies, {var})')
            match = re.search(r'jiffies\s*!=\s*(\w+)', line)
            if match:
                var = match.group(1)
                return line.replace(f'jiffies != {var}', f'time_after(jiffies, {var})')
        
        # Reemplazar: jiffies == X -> time_before_eq(jiffies, X) o !time_after(jiffies, X)
        # Usamos la negación de time_after para == 
        if 'jiffies ==' in line or '== jiffies' in line:
            match = JIFFIES_EQ.search(line)
            if match:
                var = match.group(1)
                return line.replace(f'{var} == jiffies', f'!time_after(jiffies, {var})')
            match = re.search(r'jiffies\s*==\s*(\w+)', line)
            if match:
                var = match.group(1)
                return line.replace(f'jiffies == {var}', f'!time_after(jiffies, {var})')
        
        return None
    return apply_line_transform(file_path, line_number, transform)

def fix_func_name_in_string(file_path, line_number):
    def transform(line):
        # Buscar nombres de función en strings que deberían ser __func__
        # Patrón común: "function_name:" o "function_name " o "function_name("
        # El warning de checkpatch dice específicamente el nombre de la función
        
        # Buscar strings con nombres de función seguidos de : o espacio o (
        match = FUNCTION_NAME_IN_STRING.search(line)
        if not match:
            return None
            
        func_name = match.group(1)
        
        # Solo procesar si está en una llamada a función de logging
        if not any(log_func in line for log_func in ['pr_info', 'pr_warn', 'pr_err', 'pr_debug', 'pr_emerg', 'pr_crit', 'pr_alert', 'pr_notice', 'printk', 'dev_', 'netdev_']):
            return None
        
        # Reemplazar "func_name: por "%s: y añadir __func__
        if f'"{func_name}:' in line:
            new_line = line.replace(f'"{func_name}:', '"%s:')
        elif f'"{func_name} ' in line:
            new_line = line.replace(f'"{func_name} ', '"%s ')
        elif f'"{func_name}(' in line:
            new_line = line.replace(f'"{func_name}(', '"%s(')
        else:
            return None
        
        # Insertar __func__ como argumento
        # Caso 1: "string", otros_args) → "string", __func__, otros_args)
        if re.search(r'("[^"]*")\s*,\s*', new_line):
            new_line = re.sub(r'("[^"]*")\s*,\s*', r'\1, __func__, ', new_line, count=1)
        # Caso 2: "string") sin otros args → "string", __func__)
        elif re.search(r'("[^"]*")\s*\)', new_line):
            new_line = re.sub(r'("[^"]*")\s*\)', r'\1, __func__)', new_line, count=1)
        else:
            return None
        
        return new_line
    return apply_line_transform(file_path, line_number, transform)

def fix_else_after_return(file_path, line_number):
    def callback(lines, idx):
        line = lines[idx]
        # La línea reportada es la del else
        if '} else {' in line.strip() or line.strip() == 'else {':
            # Quitar el else, dejar solo las llaves
            if '} else {' in line:
                lines[idx] = line.replace('} else {', '}')
                # Añadir apertura de bloque en nueva línea
                indent = INDENT_PATTERN.match(line).group(1)
                lines.insert(idx + 1, indent + '{\n')
                return True
            elif line.strip() == 'else {':
                # Eliminar la línea del else {
                del lines[idx]
                return True
        return False
    return apply_lines_callback(file_path, line_number, callback)

def fix_weak_attribute(file_path, line_number):
    def transform(line):
        if '__attribute__((weak))' in line:
            return line.replace('__attribute__((weak))', '__weak')
        return None
    return apply_line_transform(file_path, line_number, transform)

def fix_oom_message(file_path, line_number):
    def callback(lines, idx):
        line = lines[idx]
        # Eliminar mensajes de out of memory innecesarios
        # Típicamente son pr_err/printk después de malloc fallido
        if 'pr_err' in line or 'printk' in line or 'pr_warn' in line:
            # Verificar si el mensaje habla de memoria/allocation/buffer
            lower = line.lower()
            if any(word in lower for word in ['allocate', 'alloc', 'buffer', 'memory', 'oom']):
                del lines[idx]
                return True
        return False
    return apply_lines_callback(file_path, line_number, callback)

def fix_asm_includes(file_path, line_number):
    mapping = ASM_INCLUDE_MAP
    def transform(line):
        new = line
        for asm_inc, linux_inc in mapping.items():
            if asm_inc in new:
                new = new.replace(asm_inc, linux_inc)
        return new if new != line else None
    return apply_line_transform(file_path, line_number, transform)

def fix_initdata_placement(file_path, line_number):
    def callback(lines, idx):
        # Checkpatch reporta exactamente la línea con el problema
        line = lines[idx]
        if '__initdata' in line and ';' in line:
            # Patrón 1: static __initdata tipo variable;
            match = INITDATA_BEFORE.match(line)
            if match:
                indent, static, tipo, varname, rest = match.groups()
                rest = rest if rest.startswith(' ') else (' ' + rest if rest else '')
                lines[idx] = f'{indent}{static}{tipo} {varname.strip()} __initdata{rest};\n'
                return True
            # Patrón 2: static tipo __initdata variable = valor;
            match = INITDATA_AFTER.match(line)
            if match:
                indent, static, tipo, varname, rest = match.groups()
                rest = rest if rest.startswith(' ') else (' ' + rest if rest else '')
                lines[idx] = f'{indent}{static}{tipo} {varname.strip()} __initdata{rest};\n'
                return True
        return False
    return apply_lines_callback(file_path, line_number, callback)

def fix_missing_spdx(file_path, line_number):
    def callback(lines, idx):
        # Solo actuar si es línea 1
        if idx == 0:
            # Verificar si ya existe SPDX en las primeras líneas
            for i in range(min(3, len(lines))):
                if 'SPDX-License-Identifier' in lines[i]:
                    # Ya existe, no hacer nada
                    return False
            
            # Añadir SPDX al principio del archivo
            # Determinar el tipo de comentario según la extensión
            file_str = str(file_path)
            if file_str.endswith('.h'):
                spdx_line = '/* SPDX-License-Identifier: GPL-2.0 */\n'
            elif file_str.endswith(('.c', '.S')):
                spdx_line = '// SPDX-License-Identifier: GPL-2.0\n'
            else:
                spdx_line = '/* SPDX-License-Identifier: GPL-2.0 */\n'
            
            lines.insert(0, spdx_line)
            return True
        return False
    return apply_lines_callback(file_path, line_number, callback)

def fix_msleep_too_small(file_path, line_number):
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
    def transform(line):
        m = KMALLOC_PATTERN.search(line)
        if not m:
            return None
        return line.replace(m.group(0), f"kmalloc({m.group(1)}, GFP_KERNEL)")
    return apply_line_transform(file_path, line_number, transform)

def fix_memcpy_literal(file_path, line_number):
    def transform(line):
        m = MEMCPY_LITERAL_PATTERN.search(line)
        if not m:
            return None
        dest, literal, size = m.groups()
        return f"strscpy({dest.strip()}, \"{literal}\", {size.strip()});\n"
    return apply_line_transform(file_path, line_number, transform)

def fix_of_read_no_check(file_path, line_number):
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

def fix_strcpy_to_strscpy(file_path, line_number):
    def transform(line):
        # Reemplazar strcpy( por strscpy(
        # Necesitamos añadir el tercer parámetro (tamaño del buffer)
        # Por ahora, usamos sizeof(dest) como estimación segura
        if 'strcpy(' in line:
            # Capturar strcpy(dest, src) para convertir a strscpy(dest, src, sizeof(dest))
            match = re.search(r'strcpy\s*\(\s*([^,]+),\s*([^)]+)\)', line)
            if match:
                dest = match.group(1).strip()
                src = match.group(2).strip()
                # Reemplazar con strscpy incluyendo sizeof
                return line.replace(match.group(0), f'strscpy({dest}, {src}, sizeof({dest}))')
        return None
    return apply_line_transform(file_path, line_number, transform)

def fix_strncpy(file_path, line_number):
    def transform(line):
        m = STRNCPY_PATTERN.search(line)
        if not m:
            return None
        dest, src, size = m.groups()
        return f"strscpy({dest.strip()}, {src.strip()}, {size.strip()});\n"
    return apply_line_transform(file_path, line_number, transform)

def fix_logging_continuation(file_path, line_number):
    """Fix: Avoid logging continuation uses where feasible
    Reemplaza printk(KERN_CONT ...) por pr_cont(...)
    """
    def transform(line):
        if 'KERN_CONT' in line:
            # Reemplazar printk(KERN_CONT con pr_cont(
            return PRINTK_KERN_CONT.sub('pr_cont(', line)
        return None
    return apply_line_transform(file_path, line_number, transform)

def fix_spaces_at_start_of_line(file_path, line_number):
    """Fix: please, no spaces at the start of a line
    Elimina espacios al inicio de líneas vacías
    """
    def callback(lines, idx):
        if idx < 0 or idx >= len(lines):
            return False
        
        line = lines[idx]
        
        # Si la línea solo tiene espacios/tabs seguidos de newline, limpiarla
        if line.strip() == '' and line != '\n':
            lines[idx] = '\n'
            return True
            
        return False
    return apply_lines_callback(file_path, line_number, callback)

def fix_filename_in_file(file_path, line_number):
    """Fix: It's generally not useful to have the filename in the file
    Elimina comentarios que contienen el nombre del archivo
    """
    def callback(lines, idx):
        if idx < 0 or idx >= len(lines):
            return False
        
        line = lines[idx]
        
        # Extraer el path relativo del archivo desde el directorio del kernel
        # Por ejemplo: /home/user/kernel/linux/init/main.c -> init/main.c
        import os
        path_str = str(file_path)
        
        # Buscar el patrón linux/subdirectorio/archivo o subdirectorio/archivo
        # Intentar extraer subdirectorio/archivo.c del path completo
        if '/init/' in path_str:
            subdir = 'init'
        elif '/kernel/' in path_str:
            subdir = 'kernel'
        elif '/mm/' in path_str:
            subdir = 'mm'
        elif '/fs/' in path_str:
            subdir = 'fs'
        elif '/drivers/' in path_str:
            subdir = 'drivers'
        else:
            # Intentar extraer de forma genérica: buscar el penúltimo directorio
            parts = path_str.split('/')
            if len(parts) >= 2:
                subdir = parts[-2]
            else:
                return False
        
        filename = os.path.basename(path_str)
        
        # Buscar comentarios tipo: " * linux/init/main.c" o " * init/main.c"
        # El patrón es: " * [linux/]subdir/filename"
        pattern = rf'^\s*\*\s+(linux/)?{re.escape(subdir)}/{re.escape(filename)}\s*$'
        if re.search(pattern, line):
            # Eliminar esta línea
            del lines[idx]
            return True
            
        return False
    return apply_lines_callback(file_path, line_number, callback)


def fix_function_macro(file_path, line_number):
    """Fix: __FUNCTION__ is gcc specific, use __func__
    Converts __FUNCTION__ to __func__ (C99 standard)
    """
    def callback(lines, idx):
        if idx < 0 or idx >= len(lines):
            return False
        
        line = lines[idx]
        if '__FUNCTION__' in line:
            lines[idx] = line.replace('__FUNCTION__', '__func__')
            return True
        
        return False
    
    return apply_lines_callback(file_path, line_number, callback)

def fix_space_before_open_brace(file_path, line_number):
    """Fix: space required before the open brace '{'
    Adds space before '{' when missing
    """
    def callback(lines, idx):
        if idx < 0 or idx >= len(lines):
            return False
        
        line = lines[idx]
        # Look for patterns like: if(...){ or for(...){ or while(...){
        # Also: ){, ]{, etc.
        pattern = r'(\w|\)|\])\{'
        if re.search(pattern, line):
            lines[idx] = re.sub(pattern, r'\1 {', line)
            return True
        
        return False
    
    return apply_lines_callback(file_path, line_number, callback)

def fix_else_after_close_brace(file_path, line_number):
    """Fix: else should follow close brace '}'
    Moves else to same line as closing brace
    """
    def callback(lines, idx):
        if idx < 0 or idx >= len(lines):
            return False
        
        # Check if current line is 'else' and previous line ends with '}'
        line = lines[idx].strip()
        if line.startswith('else') and idx > 0:
            prev_line = lines[idx - 1].rstrip()
            if prev_line.endswith('}'):
                # Get indentation of else line
                else_indent = len(lines[idx]) - len(lines[idx].lstrip())
                # Merge: previous line + ' ' + current line
                lines[idx - 1] = prev_line + ' ' + line + '\n'
                # Remove current line
                del lines[idx]
                return True
        
        return False
    
    return apply_lines_callback(file_path, line_number, callback)

def fix_sizeof_struct(file_path, line_number):
    """Fix: Prefer sizeof(*p) over sizeof(struct type)
    Converts sizeof(struct foo) to sizeof(*p) when variable is present
    """
    def callback(lines, idx):
        if idx < 0 or idx >= len(lines):
            return False
        
        line = lines[idx]
        # Look for patterns like: malloc(sizeof(struct foo))
        # This is complex to do perfectly, so we do a simple version:
        # sizeof(struct \w+) where there's a pointer variable nearby
        # This is a simplified fix - only works in obvious cases
        # Pattern: variable = malloc(sizeof(struct type))
        pattern = r'(\w+)\s*=\s*(\w*alloc\w*)\s*\(\s*sizeof\s*\(\s*struct\s+\w+\s*\)\s*\)'
        match = re.search(pattern, line)
        if match:
            var_name = match.group(1)
            alloc_func = match.group(2)
            # Replace with: variable = malloc(sizeof(*variable))
            new_expr = f'{var_name} = {alloc_func}(sizeof(*{var_name}))'
            lines[idx] = re.sub(pattern, new_expr, line)
            return True
        
        return False
    
    return apply_lines_callback(file_path, line_number, callback)

def fix_consecutive_strings(file_path, line_number):
    """Fix: Consecutive strings are generally better as a single string
    Merges consecutive string literals on the same line
    """
    def callback(lines, idx):
        if idx < 0 or idx >= len(lines):
            return False
        
        line = lines[idx]
        # Look for pattern: "string1" "string2"
        # Match two or more adjacent string literals
        pattern = r'"([^"]*?)"\s+"([^"]*?)"'
        if re.search(pattern, line):
            # Merge consecutive strings
            while re.search(pattern, line):
                line = re.sub(pattern, r'"\1\2"', line)
            lines[idx] = line
            return True
        
        return False
    
    return apply_lines_callback(file_path, line_number, callback)

def fix_comparison_to_null(file_path, line_number):
    """Fix: Comparisons to NULL could be written as !variable or variable
    Converts (variable == NULL) to (!variable) and (variable != NULL) to (variable)
    """
    def callback(lines, idx):
        if idx < 0 or idx >= len(lines):
            return False
        
        line = lines[idx]
        # Pattern: variable == NULL or NULL == variable
        if '== NULL' in line or 'NULL ==' in line:
            # Replace: (variable == NULL) or (NULL == variable) with (!variable)
            line = re.sub(r'\(\s*(\w+)\s*==\s*NULL\s*\)', r'(!\1)', line)
            line = re.sub(r'\(\s*NULL\s*==\s*(\w+)\s*\)', r'(!\1)', line)
            # Also handle without explicit parens in if conditions
            line = re.sub(r'\bif\s*\(\s*(\w+)\s*==\s*NULL\s*\)', r'if (!\1)', line)
            line = re.sub(r'\bif\s*\(\s*NULL\s*==\s*(\w+)\s*\)', r'if (!\1)', line)
            lines[idx] = line
            return True
        
        if '!= NULL' in line or 'NULL !=' in line:
            # Replace: (variable != NULL) with (variable)
            line = re.sub(r'\(\s*(\w+)\s*!=\s*NULL\s*\)', r'(\1)', line)
            line = re.sub(r'\(\s*NULL\s*!=\s*(\w+)\s*\)', r'(\1)', line)
            # Also handle in if conditions
            line = re.sub(r'\bif\s*\(\s*(\w+)\s*!=\s*NULL\s*\)', r'if (\1)', line)
            line = re.sub(r'\bif\s*\(\s*NULL\s*!=\s*(\w+)\s*\)', r'if (\1)', line)
            lines[idx] = line
            return True
        
        return False
    
    return apply_lines_callback(file_path, line_number, callback)

def fix_constant_comparison(file_path, line_number):
    """Fix: Comparisons should place the constant on the right side
    Converts (5 == x) to (x == 5)
    """
    def callback(lines, idx):
        if idx < 0 or idx >= len(lines):
            return False
        
        line = lines[idx]
        # Look for pattern: (constant comparison variable)
        # This is a simplified version for numeric constants
        pattern = r'(\()\s*(\d+)\s*(==|!=|<=|>=|<|>)\s*(\w+)'
        if re.search(pattern, line):
            # Swap constant and variable
            line = re.sub(pattern, r'\1\4 \3 \2', line)
            lines[idx] = line
            return True
        
        return False
    
    return apply_lines_callback(file_path, line_number, callback)
