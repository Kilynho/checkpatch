# report.py
"""
Funciones para generación de reportes HTML
"""

import os
import html as html_module
from collections import defaultdict
import datetime
import subprocess
from utils import COMMON_CSS, percentage, bar_width, percentage_value

# --- Función para mostrar rutas relativas ---
def display_fp(fp):
    try:
        KERNEL_SUBDIR = os.path.join("../../src/kernel/linux")
        return os.path.relpath(fp, KERNEL_SUBDIR)
    except Exception:
        return fp

def generate_html_report(report_data, html_file, kernel_dir="."):

    # ...existing code...

    # --- Contadores globales sobre incidencias fijadas y saltadas ---
    files_with_errors = {f for f, issues in report_data.items() if any(i.get("fixed") for i in issues.get("error", []))}
    files_with_warnings = {f for f, issues in report_data.items() if any(i.get("fixed") for i in issues.get("warning", []))}
    files_with_errors_skipped = {f for f, issues in report_data.items() if any(not i.get("fixed") for i in issues.get("error", []))}
    files_with_warnings_skipped = {f for f, issues in report_data.items() if any(not i.get("fixed") for i in issues.get("warning", []))}
    total_files_count = len(files_with_errors | files_with_warnings)

    occ_errors_fixed = sum(1 for issues in report_data.values() for i in issues.get("error", []) if i.get("fixed"))
    occ_warnings_fixed = sum(1 for issues in report_data.values() for i in issues.get("warning", []) if i.get("fixed"))
    occ_errors_skipped = sum(1 for issues in report_data.values() for i in issues.get("error", []) if not i.get("fixed"))
    occ_warnings_skipped = sum(1 for issues in report_data.values() for i in issues.get("warning", []) if not i.get("fixed"))
    total_occ_count = occ_errors_fixed + occ_warnings_fixed

    PCT_CELL_WIDTH = 220

    html_out = []
    append = html_out.append
    timestamp = datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")

    # --- Header y CSS ---
    append("<!doctype html><html><head><meta charset='utf-8'>")
    append("<style>")
    append(COMMON_CSS)
    append("</style></head><body>")
    append(f"<h1>Informe Checkpatch Autofix <span style='font-weight:normal'>{timestamp}</span></h1>")

    # --- Tabla resumen global ---
    append("<h2>Resumen global</h2>")
    append("<table>")
    append(f"<tr><th>Estado</th><th>Ficheros</th><th style='width:{PCT_CELL_WIDTH}px;'>% Ficheros</th>"
           f"<th>Casos</th><th style='width:{PCT_CELL_WIDTH}px;'>% Casos</th></tr>")

    # Calcular totales antes del loop
    # Totales por categoría
    f_count_errors_total = len(files_with_errors | files_with_errors_skipped)
    o_count_errors_total = occ_errors_fixed + occ_errors_skipped
    f_count_warnings_total = len(files_with_warnings | files_with_warnings_skipped)
    o_count_warnings_total = occ_warnings_fixed + occ_warnings_skipped
    # Totales generales
    total_files_all = len(files_with_errors | files_with_warnings | files_with_errors_skipped | files_with_warnings_skipped)
    total_occ_all = o_count_errors_total + o_count_warnings_total
    
    # Errores corregidos (% respecto a errores procesados)
    f_count = len(files_with_errors)
    o_count = occ_errors_fixed
    f_pct = percentage(f_count, f_count_errors_total)
    o_pct = percentage(o_count, o_count_errors_total)
    f_bar = bar_width(f_count, f_count_errors_total, max_width=PCT_CELL_WIDTH - 50)
    o_bar = bar_width(o_count, o_count_errors_total, max_width=PCT_CELL_WIDTH - 50)
    append(f"<tr><td class='errors'>ERRORES CORREGIDOS</td>"
           f"<td class='num'>{f_count}</td>"
           f"<td class='num' style='width:{PCT_CELL_WIDTH}px; display:flex; align-items:center; gap:6px;'>"
           f"<span style='flex:none'>{f_pct}</span>"
           f"<div class='bar' style='flex:1;'><div class='bar-inner bar-errors' style='width:{f_bar}px'></div></div></td>"
           f"<td class='num'>{o_count}</td>"
           f"<td class='num' style='width:{PCT_CELL_WIDTH}px; display:flex; align-items:center; gap:6px;'>"
           f"<span style='flex:none'>{o_pct}</span>"
           f"<div class='bar' style='flex:1;'><div class='bar-inner bar-errors' style='width:{o_bar}px'></div></div></td></tr>")
    
    # Errores saltados (% respecto a errores procesados)
    f_count = len(files_with_errors_skipped)
    o_count = occ_errors_skipped
    f_pct = percentage(f_count, f_count_errors_total)
    o_pct = percentage(o_count, o_count_errors_total)
    f_bar = bar_width(f_count, f_count_errors_total, max_width=PCT_CELL_WIDTH - 50)
    o_bar = bar_width(o_count, o_count_errors_total, max_width=PCT_CELL_WIDTH - 50)
    append(f"<tr><td class='errors'>ERRORES SALTADOS</td>"
           f"<td class='num'>{f_count}</td>"
           f"<td class='num' style='width:{PCT_CELL_WIDTH}px; display:flex; align-items:center; gap:6px;'>"
           f"<span style='flex:none'>{f_pct}</span>"
           f"<div class='bar' style='flex:1;'><div class='bar-inner bar-errors' style='width:{f_bar}px'></div></div></td>"
           f"<td class='num'>{o_count}</td>"
           f"<td class='num' style='width:{PCT_CELL_WIDTH}px; display:flex; align-items:center; gap:6px;'>"
           f"<span style='flex:none'>{o_pct}</span>"
           f"<div class='bar' style='flex:1;'><div class='bar-inner bar-errors' style='width:{o_bar}px'></div></div></td></tr>")
    
    # Errores procesados (subtotal) - 100%
    f_pct = "100.0%"
    o_pct = "100.0%"
    f_bar = PCT_CELL_WIDTH - 50
    o_bar = PCT_CELL_WIDTH - 50
    append(f"<tr><td class='errors' style='font-weight:bold'>ERRORES PROCESADOS</td>"
           f"<td class='num' style='font-weight:bold'>{f_count_errors_total}</td>"
           f"<td class='num' style='width:{PCT_CELL_WIDTH}px; display:flex; align-items:center; gap:6px;'>"
           f"<span style='flex:none; font-weight:bold'>{f_pct}</span>"
           f"<div class='bar' style='flex:1;'><div class='bar-inner bar-errors' style='width:{f_bar}px'></div></div></td>"
           f"<td class='num' style='font-weight:bold'>{o_count_errors_total}</td>"
           f"<td class='num' style='width:{PCT_CELL_WIDTH}px; display:flex; align-items:center; gap:6px;'>"
           f"<span style='flex:none; font-weight:bold'>{o_pct}</span>"
           f"<div class='bar' style='flex:1;'><div class='bar-inner bar-errors' style='width:{o_bar}px'></div></div></td></tr>")
    
    # Warnings corregidos (% respecto a warnings procesados)
    f_count = len(files_with_warnings)
    o_count = occ_warnings_fixed
    f_pct = percentage(f_count, f_count_warnings_total)
    o_pct = percentage(o_count, o_count_warnings_total)
    f_bar = bar_width(f_count, f_count_warnings_total, max_width=PCT_CELL_WIDTH - 50)
    o_bar = bar_width(o_count, o_count_warnings_total, max_width=PCT_CELL_WIDTH - 50)
    append(f"<tr><td class='warnings'>WARNINGS CORREGIDOS</td>"
           f"<td class='num'>{f_count}</td>"
           f"<td class='num' style='width:{PCT_CELL_WIDTH}px; display:flex; align-items:center; gap:6px;'>"
           f"<span style='flex:none'>{f_pct}</span>"
           f"<div class='bar' style='flex:1;'><div class='bar-inner bar-warnings' style='width:{f_bar}px'></div></div></td>"
           f"<td class='num'>{o_count}</td>"
           f"<td class='num' style='width:{PCT_CELL_WIDTH}px; display:flex; align-items:center; gap:6px;'>"
           f"<span style='flex:none'>{o_pct}</span>"
           f"<div class='bar' style='flex:1;'><div class='bar-inner bar-warnings' style='width:{o_bar}px'></div></div></td></tr>")
    
    # Warnings saltados (% respecto a warnings procesados)
    f_count = len(files_with_warnings_skipped)
    o_count = occ_warnings_skipped
    f_pct = percentage(f_count, f_count_warnings_total)
    o_pct = percentage(o_count, o_count_warnings_total)
    f_bar = bar_width(f_count, f_count_warnings_total, max_width=PCT_CELL_WIDTH - 50)
    o_bar = bar_width(o_count, o_count_warnings_total, max_width=PCT_CELL_WIDTH - 50)
    append(f"<tr><td class='warnings'>WARNINGS SALTADOS</td>"
           f"<td class='num'>{f_count}</td>"
           f"<td class='num' style='width:{PCT_CELL_WIDTH}px; display:flex; align-items:center; gap:6px;'>"
           f"<span style='flex:none'>{f_pct}</span>"
           f"<div class='bar' style='flex:1;'><div class='bar-inner bar-warnings' style='width:{f_bar}px'></div></div></td>"
           f"<td class='num'>{o_count}</td>"
           f"<td class='num' style='width:{PCT_CELL_WIDTH}px; display:flex; align-items:center; gap:6px;'>"
           f"<span style='flex:none'>{o_pct}</span>"
           f"<div class='bar' style='flex:1;'><div class='bar-inner bar-warnings' style='width:{o_bar}px'></div></div></td></tr>")
    
    # Warnings procesados (subtotal) - 100%
    f_pct = "100.0%"
    o_pct = "100.0%"
    f_bar = PCT_CELL_WIDTH - 50
    o_bar = PCT_CELL_WIDTH - 50
    append(f"<tr><td class='warnings' style='font-weight:bold'>WARNINGS PROCESADOS</td>"
           f"<td class='num' style='font-weight:bold'>{f_count_warnings_total}</td>"
           f"<td class='num' style='width:{PCT_CELL_WIDTH}px; display:flex; align-items:center; gap:6px;'>"
           f"<span style='flex:none; font-weight:bold'>{f_pct}</span>"
           f"<div class='bar' style='flex:1;'><div class='bar-inner bar-warnings' style='width:{f_bar}px'></div></div></td>"
           f"<td class='num' style='font-weight:bold'>{o_count_warnings_total}</td>"
           f"<td class='num' style='width:{PCT_CELL_WIDTH}px; display:flex; align-items:center; gap:6px;'>"
           f"<span style='flex:none; font-weight:bold'>{o_pct}</span>"
           f"<div class='bar' style='flex:1;'><div class='bar-inner bar-warnings' style='width:{o_bar}px'></div></div></td></tr>")

    # Total corregidos (% respecto al total general)
    f_count_corrected = len(files_with_errors | files_with_warnings)
    o_count_corrected = occ_errors_fixed + occ_warnings_fixed
    f_pct = percentage(f_count_corrected, total_files_all)
    o_pct = percentage(o_count_corrected, total_occ_all)
    f_bar = bar_width(f_count_corrected, total_files_all, max_width=PCT_CELL_WIDTH - 50)
    o_bar = bar_width(o_count_corrected, total_occ_all, max_width=PCT_CELL_WIDTH - 50)
    append(f"<tr style='background:#e3f2fd'><td class='total' style='color:#1976d2'>TOTAL CORREGIDOS</td>"
           f"<td class='num'>{f_count_corrected}</td>"
           f"<td class='num' style='width:{PCT_CELL_WIDTH}px; display:flex; align-items:center; gap:6px;'>"
           f"<span style='flex:none'>{f_pct}</span>"
           f"<div class='bar' style='flex:1;'><div class='bar-inner' style='background:#42a5f5; width:{f_bar}px'></div></div></td>"
           f"<td class='num'>{o_count_corrected}</td>"
           f"<td class='num' style='width:{PCT_CELL_WIDTH}px; display:flex; align-items:center; gap:6px;'>"
           f"<span style='flex:none'>{o_pct}</span>"
           f"<div class='bar' style='flex:1;'><div class='bar-inner' style='background:#42a5f5; width:{o_bar}px'></div></div></td></tr>")
    
    # Total saltados (% respecto al total general)
    f_count_skipped = len(files_with_errors_skipped | files_with_warnings_skipped)
    o_count_skipped = occ_errors_skipped + occ_warnings_skipped
    f_pct = percentage(f_count_skipped, total_files_all)
    o_pct = percentage(o_count_skipped, total_occ_all)
    f_bar = bar_width(f_count_skipped, total_files_all, max_width=PCT_CELL_WIDTH - 50)
    o_bar = bar_width(o_count_skipped, total_occ_all, max_width=PCT_CELL_WIDTH - 50)
    append(f"<tr style='background:#e3f2fd'><td class='total' style='color:#1976d2'>TOTAL SALTADOS</td>"
           f"<td class='num' style='font-weight:bold'>{f_count_skipped}</td>"
           f"<td class='num' style='width:{PCT_CELL_WIDTH}px; display:flex; align-items:center; gap:6px;'>"
           f"<span style='flex:none; font-weight:bold'>{f_pct}</span>"
           f"<div class='bar' style='flex:1;'><div class='bar-inner' style='background:#bdbdbd; width:{f_bar}px'></div></div></td>"
           f"<td class='num'>{o_count_skipped}</td>"
           f"<td class='num' style='width:{PCT_CELL_WIDTH}px; display:flex; align-items:center; gap:6px;'>"
           f"<span style='flex:none'>{o_pct}</span>"
           f"<div class='bar' style='flex:1;'><div class='bar-inner' style='background:#42a5f5; width:{o_bar}px'></div></div></td></tr>")

    # Fila TOTAL - 100%
    f_pct = "100.0%"
    o_pct = "100.0%"
    f_bar = PCT_CELL_WIDTH - 50
    o_bar = PCT_CELL_WIDTH - 50
    append(f"<tr style='background:#e3f2fd'><td class='total' style='color:#1976d2; font-weight:bold'>TOTAL</td>"
           f"<td class='num' style='font-weight:bold'>{total_files_all}</td>"
           f"<td class='num' style='width:{PCT_CELL_WIDTH}px; display:flex; align-items:center; gap:6px;'>"
           f"<span style='flex:none; font-weight:bold'>{f_pct}</span>"
           f"<div class='bar' style='flex:1;'><div class='bar-inner' style='background:#42a5f5; width:{f_bar}px'></div></div></td>"
           f"<td class='num' style='font-weight:bold'>{total_occ_all}</td>"
           f"<td class='num' style='width:{PCT_CELL_WIDTH}px; display:flex; align-items:center; gap:6px;'>"
           f"<span style='flex:none; font-weight:bold'>{o_pct}</span>"
           f"<div class='bar' style='flex:1;'><div class='bar-inner' style='background:#42a5f5; width:{f_bar}px'></div></div></td></tr>")

    append("</table>")
    
    # Nota sobre correcciones indirectas
    append("<div style='margin: 15px 0; padding: 12px; background: #e3f2fd; border-left: 4px solid #2196F3; border-radius: 4px;'>")
    append("<strong>ℹ️ Nota:</strong> Algunos errores pueden corregirse indirectamente como efecto secundario de otras transformaciones. ")
    append("Por ejemplo, al transformar <code>simple_strtoul(str,NULL,0)</code> a <code>kstrtoul(str, NULL, 0)</code>, ")
    append("también se corrigen automáticamente los errores de espaciado alrededor de las comas. ")
    append("El contador de 'errores corregidos' refleja las correcciones directas aplicadas.")
    append("</div>")

    # --- Preparar datos por motivo ---
    error_reason_files = defaultdict(list)
    warning_reason_files = defaultdict(list)
    for f, issues in report_data.items():
        for e in issues.get("error", []):
            if e.get("fixed"):
                error_reason_files[e.get("message", "UNKNOWN")].append(f)
        for w in issues.get("warning", []):
            if w.get("fixed"):
                warning_reason_files[w.get("message", "UNKNOWN")].append(f)

    # --- Función para escribir tabla de motivos ---
    def write_reason_table(reason_files_dict, typ):
        cls = "errors" if typ=="error" else "warnings"
        section_title = "Errores" if typ=="error" else "Warnings"
        # total de casos
        total_cases = sum(len(files) for files in reason_files_dict.values())
        # total de ficheros únicos que contienen al menos un motivo
        total_files = len(set(f for files in reason_files_dict.values() for f in files))

        append(f"<h3 class='{cls}'>{section_title}</h3>")
        append(f"<table><tr><th>Motivo</th><th>Ficheros</th><th>% Ficheros</th><th>Casos</th><th>% de {typ}s</th></tr>")

        for reason, files_list in sorted(reason_files_dict.items(), key=lambda x: -len(x[1])):
            count_cases = len(files_list)
            count_files = len(set(files_list))
            pct_files = percentage(count_files, total_files)
            pct_cases = percentage(count_cases, total_cases)
            bar_files_len = bar_width(count_files, total_files, max_width=PCT_CELL_WIDTH-50)
            bar_cases_len = bar_width(count_cases, total_cases, max_width=PCT_CELL_WIDTH-50)
            reason_text = reason
            if reason_text.startswith(f"{typ.upper()}: "):
                reason_text = reason_text[len(f"{typ.upper()}: "):]
            fid = reason.replace("/", "_").replace(" ", "_")
            append(f"<tr><td>{html_module.escape(f'{typ.upper()}: {reason_text}')}</td>"
                   f"<td class='num'>{count_files}</td>"
                   f"<td class='num' style='width:{PCT_CELL_WIDTH}px; display:flex; align-items:center; gap:6px;'>"
                   f"<span style='flex:none'>{pct_files}</span>"
                   f"<div class='bar' style='flex:1;'><div class='bar-inner bar-{cls}' style='width:{bar_files_len}px'></div></div></td>"
                   f"<td class='num'><a href='#{fid}'>{count_cases}</a></td>"
                   f"<td class='num' style='width:{PCT_CELL_WIDTH}px; display:flex; align-items:center; gap:6px;'>"
                   f"<span style='flex:none'>{pct_cases}</span>"
                   f"<div class='bar' style='flex:1;'><div class='bar-inner bar-{cls}' style='width:{bar_cases_len}px'></div></div></td></tr>")
        append("</table>")

    write_reason_table(error_reason_files, "error")
    write_reason_table(warning_reason_files, "warning")

    # --- Detalle por motivo ---
    append("<h2>Detalle por motivo</h2>")
    for reason, files_list in {**error_reason_files, **warning_reason_files}.items():
        rid = reason.replace("/", "_").replace(" ", "_")
        append(f"<h4 id='{rid}' class='errors'>{html_module.escape(reason)} — {len(files_list)} casos</h4><ul>")
        file_counts = defaultdict(int)
        for fp in files_list:
            file_counts[fp] += 1
        for fp, cnt in file_counts.items():
            append(f"<li><a href='#{fp.replace('/', '_')}'>{display_fp(fp)} ({cnt})</a></li>")
        append("</ul>")
        # --- Detalle por fichero separado (mejorado: genera diffs desde backups .bak) ---
        # helper: escape and format diffs with coloring
        def _escape_html(s):
            return html_module.escape(s)

        def _format_diff_html(diff_text):
            if not diff_text or not diff_text.strip():
                return '<pre class="diff-pre" style="color:#999;">No changes</pre>'
            out = ['<pre class="diff-pre">']
            for line in diff_text.split('\n'):
                if line.startswith('+++') or line.startswith('---'):
                    out.append(f'<span style="color:#999; font-weight:bold;">{_escape_html(line)}</span>')
                elif line.startswith('@@'):
                    out.append(f'<span style="color:#2196F3; font-weight:bold;">{_escape_html(line)}</span>')
                elif line.startswith('+') and not line.startswith('+++'):
                    out.append(f'<span style="color:#4CAF50; background:#f1f8f4;">{_escape_html(line)}</span>')
                elif line.startswith('-') and not line.startswith('---'):
                    out.append(f'<span style="color:#f44336; background:#ffe6e6;">{_escape_html(line)}</span>')
                else:
                    out.append(_escape_html(line))
            out.append('</pre>')
            return '\n'.join(out)

        def _get_diff(bak_path, current_path):
            try:
                res = subprocess.run(['diff', '-u', bak_path, current_path], capture_output=True, text=True)
                return res.stdout
            except Exception:
                return ''

        # Aggregate fix stats (for 'Arreglos por Tipo' or summaries)
        fix_stats = defaultdict(int)
        for f, issues in report_data.items():
            for typ in ("error", "warning"):
                for i in issues.get(typ, []):
                    if i.get('fixed'):
                        rule = i.get('message') or i.get('rule') or 'unknown'
                        fix_stats[rule] += 1

    # Render per-file details using the new style
    append(f"<h2>Detalle por fichero</h2>")
    for f, issues in sorted(report_data.items(), key=lambda x: x[0]):
        # collect fixed entries from both error and warning
        entries = [i for typ in ("error", "warning") for i in issues.get(typ, []) if i.get('fixed')]
        if not entries:
            continue
        fid = f.replace('/', '_')
        display_name = display_fp(f)
        # compute aggregate added/removed lines from available diffs or backups
        total_added = 0
        total_removed = 0
        # try to find a .bak file for the path
        bak_path = f + '.bak'
        diff_text = None
        if os.path.exists(bak_path):
            diff_text = _get_diff(bak_path, f)
            total_added = len([l for l in diff_text.split('\n') if l.startswith('+') and not l.startswith('+++')])
            total_removed = len([l for l in diff_text.split('\n') if l.startswith('-') and not l.startswith('---')])

        append(f"<details class='file-detail' id='{fid}'><summary>{_escape_html(display_name)}"
                f"<div class='stats'><div class='stat-item'><span class='added'>+{total_added}</span> <span class='removed'>-{total_removed}</span></div>"
                f"<span class='fixed-badge'>{sum(1 for _ in entries)} fixes</span></div></summary>")

        # show combined diff if available
        if diff_text:
            append("<div class='detail-content'>")
            append(_format_diff_html(diff_text))
            append("</div>")
        else:
            # fallback: show individual small diffs per entry if present in json
            append("<div class='detail-content'>")
            for e in entries:
                dtxt = e.get('diff')
                if dtxt:
                    append(f"<details style='margin-top:6px;'><summary>Diff línea {e.get('line')}</summary>")
                    append(_format_diff_html(dtxt))
                    append("</details>")
            append("</div>")

        append("</details>")
    append("</body></html>")

    with open(html_file, "w", encoding="utf-8") as f:
        f.write("\n".join(html_out))

def summarize_results(report_data, json_file, html_file, kernel_dir="."):
    """
    Muestra en consola un resumen de los resultados de fixes aplicados.
    """
    # --- Depuración mínima ---
    total_issues = sum(len(v.get("error", [])) + len(v.get("warning", [])) for v in report_data.values())

    # Contadores
    modified_files = 0
    errors_fixed = 0
    errors_skipped = 0
    warnings_fixed = 0
    warnings_skipped = 0

    for f, issues in report_data.items():
        file_modified = any(i.get("fixed") for typ in ["error", "warning"] for i in issues.get(typ, []))
        if file_modified:
            modified_files += 1

        for typ in ["error", "warning"]:
            for i in issues.get(typ, []):
                if i.get("fixed"):
                    if typ == "error":
                        errors_fixed += 1
                    else:
                        warnings_fixed += 1
                else:
                    if typ == "error":
                        errors_skipped += 1
                    else:
                        warnings_skipped += 1

    total_errors = errors_fixed + errors_skipped
    total_warnings = warnings_fixed + warnings_skipped
    total_total = total_errors + total_warnings
    total_corrected = errors_fixed + warnings_fixed
    total_skipped = errors_skipped + warnings_skipped

    print("\n[AUTOFIX] Resumen de correcciones")
    print(f"[AUTOFIX] Ficheros modificados: {modified_files}")
    for f, issues in report_data.items():
        if any(i.get("fixed") for typ in ["error", "warning"] for i in issues.get(typ, [])):
            f = display_fp(f)
            print(f"[AUTOFIX]  - {f}")
    print(f"[AUTOFIX] Errores procesados: {total_errors}")
    print(f"[AUTOFIX]  - Corregidos: {errors_fixed} ({(errors_fixed/total_errors*100 if total_errors else 0):.1f}%)")
    print(f"[AUTOFIX]  - Saltados : {errors_skipped} ({(errors_skipped/total_errors*100 if total_errors else 0):.1f}%)")
    print(f"[AUTOFIX] Warnings procesados: {total_warnings}")
    print(f"[AUTOFIX]  - Corregidos: {warnings_fixed} ({(warnings_fixed/total_warnings*100 if total_warnings else 0):.1f}%)")
    print(f"[AUTOFIX]  - Saltados : {warnings_skipped} ({(warnings_skipped/total_warnings*100 if total_warnings else 0):.1f}%)")
    print(f"[AUTOFIX] Total procesados: {total_total}")
    print(f"[AUTOFIX]  - Corregidos: {total_corrected} ({(total_corrected/total_warnings*100 if total_corrected else 0):.1f}%)")
    print(f"[AUTOFIX]  - Saltados : {total_skipped} ({(total_skipped/total_warnings*100 if total_skipped else 0):.1f}%)")
    print(f"[AUTOFIX] ✔ Análisis terminado {json_file}")
    print(f"[AUTOFIX] ✔ Informe HTML generado : {html_file}")
    print(f"[AUTOFIX] ✔ JSON generado: {json_file}")


# ============================
# Funciones del Analyzer
# ============================

def generate_analyzer_html(analysis_data, html_file):
    """
    Genera el reporte HTML del analyzer.
    
    Args:
        analysis_data: Diccionario con summary, global_counts, error_reasons, warning_reasons, etc.
        html_file: Ruta del archivo HTML de salida
    """
    summary = analysis_data["summary"]
    global_counts = analysis_data["global_counts"]
    error_reasons = analysis_data["error_reasons"]
    warning_reasons = analysis_data["warning_reasons"]
    error_reason_files = analysis_data["error_reason_files"]
    warning_reason_files = analysis_data["warning_reason_files"]
    file_outputs = analysis_data.get("file_outputs", {})
    kernel_dir = analysis_data.get("kernel_dir", "")
    
    html_out = []
    append = html_out.append
    timestamp = datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    
    # Helper para rutas relativas
    def get_relative_path(fp):
        if kernel_dir:
            try:
                return os.path.relpath(fp, kernel_dir)
            except:
                return fp
        return fp
    
    # Header y CSS
    append("<!doctype html><html><head><meta charset='utf-8'>")
    append("<style>")
    append(COMMON_CSS)
    append("</style></head><body>")
    append(f"<h1>Informe Checkpatch Analyzer <span style='font-weight:normal'>{timestamp}</span></h1>")
    
    # ============================
    # RESUMEN GLOBAL
    # ============================
    total_files_count = sum(
        len(summary[func]["errors"]) + 
        len(summary[func]["warnings"]) + 
        len(summary[func]["correct"]) 
        for func in summary
    )
    
    files_errors = sum(len(summary[func]["errors"]) for func in summary)
    files_warnings = sum(len(summary[func]["warnings"]) for func in summary)
    files_correct = sum(len(summary[func]["correct"]) for func in summary)
    
    occ_errors = sum(error_reasons.values())
    occ_warnings = sum(warning_reasons.values())
    occ_correct = global_counts["correct"]
    
    total_occ_count = occ_errors + occ_warnings + occ_correct
    
    PCT_CELL_WIDTH = 220
    
    append("<h2>Resumen global</h2>")
    append("<table>")
    append(f"<tr><th>Estado</th><th>Ficheros</th>"
           f"<th style='width:{PCT_CELL_WIDTH}px;'>% Ficheros</th>"
           f"<th>Casos</th>"
           f"<th style='width:{PCT_CELL_WIDTH}px;'>% Casos</th></tr>")
    
    for key, cls, f_count, o_count in [
        ("errors", "errors", files_errors, occ_errors),
        ("warnings", "warnings", files_warnings, occ_warnings),
        ("correct", "correct", files_correct, occ_correct)
    ]:
        f_pct = percentage(f_count, total_files_count)
        o_pct = percentage(o_count, total_occ_count)
        f_pct_val = percentage_value(f_count, total_files_count)
        o_pct_val = percentage_value(o_count, total_occ_count)
        
        append(f"<tr><td class='{cls}'>{key.upper()}</td>"
               f"<td class='num'>{f_count}</td>"
               f"<td class='num' style='width:{PCT_CELL_WIDTH}px; display:flex; align-items:center; gap:6px;'>"
               f"<span style='flex:none'>{f_pct}</span>"
               f"<div class='bar' style='flex:1;'><div class='bar-inner bar-{cls}' style='width:{f_pct_val}%'></div></div>"
               f"</td>"
               f"<td class='num'>{o_count}</td>"
               f"<td class='num' style='width:{PCT_CELL_WIDTH}px; display:flex; align-items:center; gap:6px;'>"
               f"<span style='flex:none'>{o_pct}</span>"
               f"<div class='bar' style='flex:1;'><div class='bar-inner bar-{cls}' style='width:{o_pct_val}%'></div></div>"
               f"</td></tr>")
    
    append(f"<tr><td class='total'>TOTAL</td>"
           f"<td class='num'>{total_files_count}</td>"
           f"<td class='num' style='width:{PCT_CELL_WIDTH}px; display:flex; align-items:center; gap:6px;'>"
           f"<span style='flex:none'>100%</span>"
           f"<div class='bar' style='flex:1;'><div class='bar-inner bar-total' style='width:100%'></div></div>"
           f"</td>"
           f"<td class='num'>{total_occ_count}</td>"
           f"<td class='num' style='width:{PCT_CELL_WIDTH}px; display:flex; align-items:center; gap:6px;'>"
           f"<span style='flex:none'>100%</span>"
           f"<div class='bar' style='flex:1;'><div class='bar-inner bar-total' style='width:100%'></div></div>"
           f"</td></tr>")
    append("</table>")
    
    # ============================
    # RESUMEN POR MOTIVO - ERRORES
    # ============================
    if error_reasons:
        append("<h3 class='errors'>Errores</h3>")
        append("<table>")
        append(f"<tr><th>Motivo</th><th>Ficheros</th>"
               f"<th style='width:{PCT_CELL_WIDTH}px;'>% Ficheros</th>"
               f"<th>Casos</th><th style='width:{PCT_CELL_WIDTH}px;'>% de errors</th></tr>")
        
        # Calcular totales para porcentajes
        all_error_files = set()
        for fp_list in error_reason_files.values():
            for fp, _ in fp_list:
                all_error_files.add(fp)
        total_error_files = len(all_error_files)
        total_error_cases = sum(error_reasons.values())
        
        for reason, count in sorted(error_reasons.items(), key=lambda x: -x[1]):
            files_for_reason = set(fp for fp, _ in error_reason_files.get(reason, []))
            num_files = len(files_for_reason)
            
            pct_files = percentage(num_files, total_error_files)
            pct_cases = percentage(count, total_error_cases)
            pct_files_val = percentage_value(num_files, total_error_files)
            pct_cases_val = percentage_value(count, total_error_cases)
            
            # Helper para generar ID único
            import hashlib
            def safe_id(text):
                h = hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]
                return f"id_{h}"
            
            reason_id = safe_id("ERROR:" + reason)
            
            append(f"<tr><td>ERROR: {html_module.escape(reason)}</td>"
                   f"<td class='num'>{num_files}</td>"
                   f"<td class='num' style='width:{PCT_CELL_WIDTH}px; display:flex; align-items:center; gap:6px;'>"
                   f"<span style='flex:none'>{pct_files}</span>"
                   f"<div class='bar' style='flex:1;'><div class='bar-inner bar-errors' style='width:{pct_files_val}%'></div></div>"
                   f"</td>"
                   f"<td class='num'><a href='detail-reason.html#{reason_id}'>{count}</a></td>"
                   f"<td class='num' style='width:{PCT_CELL_WIDTH}px; display:flex; align-items:center; gap:6px;'>"
                   f"<span style='flex:none'>{pct_cases}</span>"
                   f"<div class='bar' style='flex:1;'><div class='bar-inner bar-errors' style='width:{pct_cases_val}%'></div></div>"
                   f"</td></tr>")
        append("</table>")
    
    # ============================
    # RESUMEN POR MOTIVO - WARNINGS
    # ============================
    if warning_reasons:
        append("<h3 class='warnings'>Warnings</h3>")
        append("<table>")
        append(f"<tr><th>Motivo</th><th>Ficheros</th>"
               f"<th style='width:{PCT_CELL_WIDTH}px;'>% Ficheros</th>"
               f"<th>Casos</th><th style='width:{PCT_CELL_WIDTH}px;'>% de warnings</th></tr>")
        
        # Calcular totales para porcentajes
        all_warning_files = set()
        for fp_list in warning_reason_files.values():
            for fp, _ in fp_list:
                all_warning_files.add(fp)
        total_warning_files = len(all_warning_files)
        total_warning_cases = sum(warning_reasons.values())
        
        for reason, count in sorted(warning_reasons.items(), key=lambda x: -x[1]):
            files_for_reason = set(fp for fp, _ in warning_reason_files.get(reason, []))
            num_files = len(files_for_reason)
            
            pct_files = percentage(num_files, total_warning_files)
            pct_cases = percentage(count, total_warning_cases)
            pct_files_val = percentage_value(num_files, total_warning_files)
            pct_cases_val = percentage_value(count, total_warning_cases)
            
            # Helper para generar ID único
            import hashlib
            def safe_id(text):
                h = hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]
                return f"id_{h}"
            
            reason_id = safe_id("WARNING:" + reason)
            
            append(f"<tr><td>WARNING: {html_module.escape(reason)}</td>"
                   f"<td class='num'>{num_files}</td>"
                   f"<td class='num' style='width:{PCT_CELL_WIDTH}px; display:flex; align-items:center; gap:6px;'>"
                   f"<span style='flex:none'>{pct_files}</span>"
                   f"<div class='bar' style='flex:1;'><div class='bar-inner bar-warnings' style='width:{pct_files_val}%'></div></div>"
                   f"</td>"
                   f"<td class='num'><a href='detail-reason.html#{reason_id}'>{count}</a></td>"
                   f"<td class='num' style='width:{PCT_CELL_WIDTH}px; display:flex; align-items:center; gap:6px;'>"
                   f"<span style='flex:none'>{pct_cases}</span>"
                   f"<div class='bar' style='flex:1;'><div class='bar-inner bar-warnings' style='width:{pct_cases_val}%'></div></div>"
                   f"</td></tr>")
        append("</table>")
    
    append("</body></html>")
    
    # Escribir archivo
    with open(html_file, "w", encoding="utf-8") as f:
        f.write("\n".join(html_out))


def generate_detail_reason_html(analysis_data, html_file):
    """Genera detail-reason.html con el análisis detallado por motivo."""
    import hashlib
    
    def safe_id(text):
        h = hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]
        return f"id_{h}"
    
    error_reasons = analysis_data["error_reasons"]
    warning_reasons = analysis_data["warning_reasons"]
    error_reason_files = analysis_data["error_reason_files"]
    warning_reason_files = analysis_data["warning_reason_files"]
    kernel_dir = analysis_data.get("kernel_dir", "")
    
    def get_relative_path(fp):
        if kernel_dir:
            try:
                return os.path.relpath(fp, kernel_dir)
            except:
                return fp
        return fp
    
    html_out = []
    append = html_out.append
    
    # Header minimalista
    timestamp = datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    append("<!doctype html><html><head><meta charset='utf-8'>")
    append("<style>")
    append(COMMON_CSS)
    append("</style></head><body>")
    append(f"<h1>Informe Checkpatch - Detalle por motivo <span style='font-weight:normal'>{timestamp}</span></h1>")
    
    # ERRORES - Detallado
    if error_reasons:
        append("<h2 class='errors'>Detalle por motivo - Errores</h2>")
        for reason in sorted(error_reasons.keys()):
            count = error_reasons[reason]
            reason_id = safe_id("ERROR:" + reason)
            files_for_reason = sorted(set(fp for fp, _ in error_reason_files.get(reason, [])))
            
            append(f"<h4 id='{reason_id}' class='errors'>ERROR: {html_module.escape(reason)}</h4>")
            append(f"Ficheros afectados: {len(files_for_reason)} | Total casos: {count}")
            append("<ul>")
            for fp in files_for_reason:
                lines = sorted(set(line for f, line in error_reason_files.get(reason, []) if f == fp))
                rel_path = get_relative_path(fp)
                file_id = safe_id("FILE:" + fp)
                append(f"<li><a href='detail-file.html#{file_id}'>{rel_path}</a> - líneas {', '.join(map(str, lines))}</li>")
            append("</ul>")
    
    # WARNINGS - Detallado
    if warning_reasons:
        append("<h2 class='warnings'>Detalle por motivo - Warnings</h2>")
        for reason in sorted(warning_reasons.keys()):
            count = warning_reasons[reason]
            reason_id = safe_id("WARNING:" + reason)
            files_for_reason = sorted(set(fp for fp, _ in warning_reason_files.get(reason, [])))
            
            append(f"<h4 id='{reason_id}' class='warnings'>WARNING: {html_module.escape(reason)}</h4>")
            append(f"Ficheros afectados: {len(files_for_reason)} | Total casos: {count}")
            append("<ul>")
            for fp in files_for_reason:
                lines = sorted(set(line for f, line in warning_reason_files.get(reason, []) if f == fp))
                rel_path = get_relative_path(fp)
                file_id = safe_id("FILE:" + fp)
                append(f"<li><a href='detail-file.html#{file_id}'>{rel_path}</a> - líneas {', '.join(map(str, lines))}</li>")
            append("</ul>")
    
    append("</body></html>")
    
    with open(html_file, "w", encoding="utf-8") as f:
        f.write("\n".join(html_out))


def generate_detail_file_html(analysis_data, html_file):
    """Genera detail-file.html con el análisis detallado por fichero."""
    import hashlib
    
    def safe_id(text):
        h = hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]
        return f"id_{h}"
    
    def colorize_output(text):
        """Coloriza el output del checkpatch: ERROR en rojo, WARNING en naranja, + en verde, # en gris."""
        lines = text.split('\n')
        colored_lines = []
        for line in lines:
            escaped_line = html_module.escape(line)
            if line.startswith('ERROR:'):
                colored_lines.append(f"<span style='color: #d32f2f; font-weight: bold;'>{escaped_line}</span>")
            elif line.startswith('WARNING:'):
                colored_lines.append(f"<span style='color: #f57c00; font-weight: bold;'>{escaped_line}</span>")
            elif line.startswith('+'):
                colored_lines.append(f"<span style='color: #2e7d32;'>{escaped_line}</span>")
            elif line.startswith('#'):
                colored_lines.append(f"<span style='color: #757575;'>{escaped_line}</span>")
            else:
                colored_lines.append(escaped_line)
        return '\n'.join(colored_lines)
    
    file_outputs = analysis_data.get("file_outputs", {})
    kernel_dir = analysis_data.get("kernel_dir", "")
    error_reason_files = analysis_data["error_reason_files"]
    warning_reason_files = analysis_data["warning_reason_files"]
    
    def get_relative_path(fp):
        if kernel_dir:
            try:
                return os.path.relpath(fp, kernel_dir)
            except:
                return fp
        return fp
    
    html_out = []
    append = html_out.append
    timestamp = datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    
    # Helper para rutas relativas
    def get_relative_path_helper(fp):
        if kernel_dir:
            try:
                return os.path.relpath(fp, kernel_dir)
            except:
                return fp
        return fp
    
    # Header y CSS
    append("<!doctype html><html><head><meta charset='utf-8'>")
    append("<style>")
    append(COMMON_CSS)
    append("</style></head><body>")
    append(f"<h1>Informe Checkpatch - Detalle por fichero <span style='font-weight:normal'>{timestamp}</span></h1>")
    
    # JavaScript para abrir el desplegable al llegar por ancla
    append("<script>")
    append("document.addEventListener('DOMContentLoaded', function() {")
    append("  const hash = window.location.hash.substring(1);")
    append("  if (hash) {")
    append("    const element = document.getElementById(hash);")
    append("    if (element && element.tagName === 'SUMMARY') {")
    append("      element.parentElement.open = true;")
    append("      element.scrollIntoView({ behavior: 'smooth', block: 'start' });")
    append("    }")
    append("  }")
    append("});")
    append("</script>")
    
    # ============================
    # DETALLE POR FICHERO
    # ============================
    # Agrupar issues por fichero
    file_issues = {}  # file_path -> [(reason, line, is_error), ...]
    for reason, issues in error_reason_files.items():
        for fp, line in issues:
            if fp not in file_issues:
                file_issues[fp] = []
            file_issues[fp].append((reason, line, True))
    
    for reason, issues in warning_reason_files.items():
        for fp, line in issues:
            if fp not in file_issues:
                file_issues[fp] = []
            file_issues[fp].append((reason, line, False))
    
    append("<h2>Detalle por fichero</h2>")
    
    for fp in sorted(file_issues.keys()):
        file_id = safe_id("FILE:" + fp)
        rel_path = get_relative_path_helper(fp)
        
        issues = file_issues[fp]
        errors = [i for i in issues if i[2]]
        warnings = [i for i in issues if not i[2]]
        
        append(f"<details class='file-detail'>")
        append(f"<summary id='{file_id}'>")
        append(f"<strong>{rel_path}</strong>")
        append(f"<span class='stats'>")
        if errors:
            append(f"<span class='stat-item'><span class='errors'>{len(errors)} errores</span></span>")
        if warnings:
            append(f"<span class='stat-item'><span class='warnings'>{len(warnings)} warnings</span></span>")
        append(f"<span class='stat-item'>Total: {len(issues)}</span>")
        append(f"</span>")
        append(f"</summary>")
        append(f"<div class='detail-content'>")
        
        # Output del checkpatch con colores
        if fp in file_outputs:
            output = file_outputs[fp]
            colored_output = colorize_output(output)
            append(f"<pre class='diff-pre'>{colored_output}</pre>")
        else:
            append(f"<p><em>Sin salida disponible</em></p>")
        
        append(f"</div>")
        append(f"</details>")
    
    append("</body></html>")
    
    with open(html_file, "w", encoding="utf-8") as f:
        f.write("\n".join(html_out))


def generate_dashboard_html(html_file):
    """Genera dashboard.html con navegación entre reportes."""
    html_out = []
    append = html_out.append
    
    append("""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Checkpatch Dashboard</title>
  <style>
    :root {
      --bg: #f6f7fb;
      --panel: #ffffff;
      --text: #1f2742;
      --muted: #6c7791;
      --accent: #2d7df6;
      --accent-strong: #1c66d8;
      --border: #dce3ef;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Inter", "Segoe UI", system-ui, sans-serif;
      background: var(--bg);
      color: var(--text);
    }
    header {
      position: sticky;
      top: 0;
      z-index: 10;
      backdrop-filter: blur(8px);
      background: rgba(246,247,251,0.9);
      border-bottom: 1px solid var(--border);
      padding: 12px 18px 8px;
    }
    .top-row {
      display: flex;
      align-items: center;
      gap: 16px;
    }
    h1 {
      margin: 0;
      font-size: 18px;
      letter-spacing: 0.4px;
      color: var(--text);
      flex: 1;
    }
    nav {
      display: inline-flex;
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 4px;
      gap: 6px;
      box-shadow: 0 6px 18px rgba(0,0,0,0.06);
    }
    .tab {
      border: none;
      background: transparent;
      color: var(--muted);
      padding: 10px 14px;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .tab:hover { color: var(--text); }
    .tab.active {
      background: linear-gradient(135deg, var(--accent), var(--accent-strong));
      color: #ffffff;
      box-shadow: 0 8px 18px rgba(44,124,246,0.28);
    }
    .breadcrumb {
      margin: 10px 0 4px;
      font-size: 13px;
      color: var(--muted);
      display: flex;
      gap: 6px;
      align-items: center;
      flex-wrap: wrap;
    }
    .breadcrumb a {
      color: var(--accent);
      text-decoration: none;
      font-weight: 600;
    }
    .breadcrumb a:hover { text-decoration: underline; }
    .crumb-sep { color: var(--muted); }
    main {
      min-height: calc(100vh - 110px);
      padding: 14px 18px 18px;
    }
    #view {
      width: 100%;
      height: calc(100vh - 120px);
      border: 1px solid var(--border);
      border-radius: 12px;
      background: var(--panel);
      box-shadow: 0 10px 26px rgba(0,0,0,0.12);
    }
  </style>
</head>
<body>
  <header>
    <div class="top-row">
      <h1>Checkpatch Dashboard</h1>
      <nav>
        <button class="tab active" data-target="analyzer">Analyzer</button>
        <button class="tab" data-target="autofix">Autofix</button>
        <button class="tab" data-target="compile">Compile</button>
      </nav>
    </div>
    <div class="breadcrumb" id="breadcrumb">Analyzer</div>
  </header>
  <main>
    <iframe id="view" src="analyzer.html" title="Checkpatch view"></iframe>
  </main>

  <script>
    const routes = {
      analyzer: { url: 'analyzer.html', label: 'Analyzer', breadcrumb: [{ label: 'Analyzer', target: 'analyzer' }] },
      autofix: { url: 'autofix.html', label: 'Autofix', breadcrumb: [{ label: 'Autofix', target: 'autofix' }] },
      compile: { url: 'compile.html', label: 'Compile', breadcrumb: [{ label: 'Compile', target: 'compile' }] },
      'detail-reason': { url: 'detail-reason.html', label: 'Detalle por motivo', breadcrumb: [{ label: 'Analyzer', target: 'analyzer' }, { label: 'Detalle por motivo', target: 'detail-reason' }] },
      'detail-file': { url: 'detail-file.html', label: 'Detalle por fichero', breadcrumb: [{ label: 'Analyzer', target: 'analyzer' }, { label: 'Detalle por motivo', target: 'detail-reason' }, { label: 'Detalle por fichero', target: 'detail-file' }] },
      'autofix-detail-reason': { url: 'autofix-detail-reason.html', label: 'Detalle por tipo de fix', breadcrumb: [{ label: 'Autofix', target: 'autofix' }, { label: 'Detalle por tipo de fix', target: 'autofix-detail-reason' }] },
      'autofix-detail-file': { url: 'autofix-detail-file.html', label: 'Detalle por fichero', breadcrumb: [{ label: 'Autofix', target: 'autofix' }, { label: 'Detalle por tipo de fix', target: 'autofix-detail-reason' }, { label: 'Detalle por fichero', target: 'autofix-detail-file' }] }
    };

    const view = document.getElementById('view');
    const breadcrumb = document.getElementById('breadcrumb');
    const tabButtons = Array.from(document.querySelectorAll('.tab'));
    let currentContext = 'analyzer'; // Tracker del contexto actual

    function labelFromUrl(url) {
      const file = url.split('/').pop().replace('.html', '');
      if (routes[file]?.label) return routes[file].label;
      return file.replace(/[-_]/g, ' ');
    }

    function setBreadcrumb(path) {
      breadcrumb.innerHTML = path.map((item, idx) => {
        const isLast = idx === path.length - 1;
        if (isLast) return `<span>${item.label}</span>`;
        return `<a href="#" data-target="${item.target}">${item.label}</a><span class="crumb-sep">›</span>`;
      }).join(' ');

      breadcrumb.querySelectorAll('a').forEach(a => {
        a.addEventListener('click', (e) => {
          e.preventDefault();
          const target = e.currentTarget.dataset.target;
          const route = routes[target];
          if (route?.breadcrumb) {
            navigate(target, route.breadcrumb);
          } else {
            navigate(target, [{ label: routes[target]?.label || labelFromUrl(target), target }]);
          }
        });
      });
    }

    function navigate(targetKeyOrUrl, trail) {
      const route = routes[targetKeyOrUrl];
      const url = route ? route.url : targetKeyOrUrl;
      view.src = url;
      setBreadcrumb(trail);
      tabButtons.forEach(btn => btn.classList.toggle('active', btn.dataset.target === targetKeyOrUrl));
      
      // Actualizar contexto según la navegación
      if (targetKeyOrUrl === 'analyzer' || targetKeyOrUrl === 'detail-reason' || targetKeyOrUrl === 'detail-file') {
        currentContext = 'analyzer';
      } else if (targetKeyOrUrl === 'autofix' || targetKeyOrUrl === 'autofix-detail-reason' || targetKeyOrUrl === 'autofix-detail-file') {
        currentContext = 'autofix';
      } else if (targetKeyOrUrl === 'compile') {
        currentContext = 'compile';
      }
    }

    view.addEventListener('load', () => {
      const doc = view.contentDocument;
      if (!doc) return;
      doc.querySelectorAll('a[href]').forEach(a => {
        const href = a.getAttribute('href');
        if (!href || href.startsWith('http')) return;
        a.addEventListener('click', (e) => {
          e.preventDefault();
          const [filepath, anchor] = href.split('#');
          const target = filepath.replace('.html', '');
          
          // Si es un enlace a la misma página (con anchor), mantener en la misma vista
          if (!filepath || filepath === '' || filepath === '#') {
            if (anchor) {
              view.src = view.src.split('#')[0] + '#' + anchor;
            }
            return;
          }
          
          // Determinar el contexto correcto basado en dónde viene el clic
          let route = routes[target];
          if (!route) {
            const label = labelFromUrl(target);
            navigate(target, [{ label, target }]);
            return;
          }
          
          // Si la página de origen es autofix*, usar contexto autofix
          const currentPage = view.src.split('/').pop().replace('.html', '');
          if (currentPage.startsWith('autofix')) {
            currentContext = 'autofix';
            // Reconstruir breadcrumb para contexto autofix
            if (target === 'autofix-detail-reason' || target === 'autofix-detail-file') {
              route = routes[target];
              navigate(target, route.breadcrumb);
            } else {
              navigate(target, route.breadcrumb);
            }
          } else {
            currentContext = 'analyzer';
            navigate(target, route.breadcrumb);
          }
          
          if (anchor) {
            setTimeout(() => {
              const elem = view.contentDocument?.getElementById(anchor);
              if (elem) elem.scrollIntoView();
            }, 100);
          }
        });
      });
    });

    tabButtons.forEach(btn => {
      btn.addEventListener('click', (e) => {
        const target = e.currentTarget.dataset.target;
        const route = routes[target];
        if (route?.breadcrumb) {
          navigate(target, route.breadcrumb);
        } else {
          navigate(target, [{ label: btn.textContent, target }]);
        }
      });
    });

    navigate('analyzer', [{ label: 'Analyzer', target: 'analyzer' }]);
  </script>
</body>
</html>""")
    
    with open(html_file, "w", encoding="utf-8") as f:
        f.write("\n".join(html_out))

def generate_autofix_html(fixed_data, html_file):
    """Genera autofix.html simplificado - solo resumen global"""
    
    files_with_fixed = {f for f, issues in fixed_data.items() if any(i.get("fixed") for i in issues.get("error", []) + issues.get("warning", []))}
    files_with_skipped = {f for f, issues in fixed_data.items() if any(not i.get("fixed") for i in issues.get("error", []) + issues.get("warning", []))}
    
    occ_errors_fixed = sum(1 for issues in fixed_data.values() for i in issues.get("error", []) if i.get("fixed"))
    occ_warnings_fixed = sum(1 for issues in fixed_data.values() for i in issues.get("warning", []) if i.get("fixed"))
    occ_errors_skipped = sum(1 for issues in fixed_data.values() for i in issues.get("error", []) if not i.get("fixed"))
    occ_warnings_skipped = sum(1 for issues in fixed_data.values() for i in issues.get("warning", []) if not i.get("fixed"))
    total_occ_fixed = occ_errors_fixed + occ_warnings_fixed
    total_occ = total_occ_fixed + occ_errors_skipped + occ_warnings_skipped
    
    total_files = len(files_with_fixed | files_with_skipped)
    total_files_fixed = len(files_with_fixed)
    
    html_out = []
    append = html_out.append
    timestamp = datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    
    files_errors_fixed = len({f for f, issues in fixed_data.items() if any(i.get("fixed") for i in issues.get("error", []))})
    files_errors_total = len({f for f, issues in fixed_data.items() if issues.get("error")})
    files_warnings_fixed = len({f for f, issues in fixed_data.items() if any(i.get("fixed") for i in issues.get("warning", []))})
    files_warnings_total = len({f for f, issues in fixed_data.items() if issues.get("warning")})
    files_errors_skipped = len({f for f, issues in fixed_data.items() if any(not i.get('fixed') for i in issues.get('error', []))})
    files_warnings_skipped = len({f for f, issues in fixed_data.items() if any(not i.get('fixed') for i in issues.get('warning', []))})
    
    # Calcular barras y porcentajes
    pct_files_errors = (100.0 * files_errors_fixed) / max(1, files_errors_total)
    pct_occ_errors = (100.0 * occ_errors_fixed) / max(1, occ_errors_fixed + occ_errors_skipped)
    pct_files_warnings = (100.0 * files_warnings_fixed) / max(1, files_warnings_total)
    pct_occ_warnings = (100.0 * occ_warnings_fixed) / max(1, occ_warnings_fixed + occ_warnings_skipped)
    pct_total_files = (100.0 * total_files_fixed) / max(1, total_files)
    pct_total_occ = (100.0 * total_occ_fixed) / max(1, total_occ)
    
    append("<!doctype html><html><head><meta charset='utf-8'>")
    append("<style>")
    append(COMMON_CSS)
    append(".exec-summary { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }")
    append(".exec-box { padding: 15px; border-radius: 6px; border-left: 4px solid; }")
    append(".exec-box.success { background: #c8e6c9; border-color: #2e7d32; }")
    append(".exec-box.partial { background: #fff3e0; border-color: #f57c00; }")
    append(".exec-box h3 { margin: 0 0 10px 0; font-size: 14px; }")
    append(".exec-box .value { font-size: 24px; font-weight: bold; margin-bottom: 5px; }")
    append(".exec-box .percent { font-size: 12px; color: #555; }")
    append("</style></head><body>")
    append(f"<h1>Informe Checkpatch Autofix <span style='font-weight:normal'>{timestamp}</span></h1>")
    append("<div class='exec-summary'>")
    append(f"<div class='exec-box success'><h3>🎯 Tasa de Éxito</h3><div class='value'>{pct_total_occ:.1f}%</div><div class='percent'>{total_occ_fixed}/{total_occ} issues</div></div>")
    append(f"<div class='exec-box partial'><h3>📁 Ficheros Procesados</h3><div class='value'>{total_files_fixed}/{total_files}</div><div class='percent'>Con al menos 1 fix</div></div>")
    append("</div>")
    append("<h2>Resumen global</h2>")
    append("<table>")
    append("<tr><th>Estado</th><th>Ficheros</th><th style='width:220px;'>% Ficheros</th><th>Casos</th><th style='width:220px;'>% Casos</th></tr>")
    
    MAX_WIDTH = 170
    bar_files_errors = int(pct_files_errors * MAX_WIDTH / 100)
    bar_occ_errors = int(pct_occ_errors * MAX_WIDTH / 100)
    bar_files_warnings = int(pct_files_warnings * MAX_WIDTH / 100)
    bar_occ_warnings = int(pct_occ_warnings * MAX_WIDTH / 100)
    bar_total_files = int(pct_total_files * MAX_WIDTH / 100)
    bar_total_occ = int(pct_total_occ * MAX_WIDTH / 100)
    
    append(f"<tr><td class='errors'>ERRORES CORREGIDOS</td><td class='num'>{files_errors_fixed}</td><td class='num' style='width:220px; display:flex; align-items:center; gap:6px;'><span style='flex:none'>{pct_files_errors:.1f}%</span><div class='bar' style='flex:1;'><div class='bar-inner bar-errors' style='width:{bar_files_errors}px'></div></div></td><td class='num'>{occ_errors_fixed}</td><td class='num' style='width:220px; display:flex; align-items:center; gap:6px;'><span style='flex:none'>{pct_occ_errors:.1f}%</span><div class='bar' style='flex:1;'><div class='bar-inner bar-errors' style='width:{bar_occ_errors}px'></div></div></td></tr>")
    
    append(f"<tr><td class='errors'>ERRORES SALTADOS</td><td class='num'>{files_errors_skipped}</td><td class='num' style='width:220px; display:flex; align-items:center; gap:6px;'><span style='flex:none'>{100.0 - pct_files_errors:.1f}%</span><div class='bar' style='flex:1;'><div class='bar-inner bar-errors' style='width:{MAX_WIDTH - bar_files_errors}px'></div></div></td><td class='num'>{occ_errors_skipped}</td><td class='num' style='width:220px; display:flex; align-items:center; gap:6px;'><span style='flex:none'>{100.0 - pct_occ_errors:.1f}%</span><div class='bar' style='flex:1;'><div class='bar-inner bar-errors' style='width:{MAX_WIDTH - bar_occ_errors}px'></div></div></td></tr>")
    
    append(f"<tr><td class='errors' style='font-weight:bold'>ERRORES PROCESADOS</td><td class='num' style='font-weight:bold'>{files_errors_total}</td><td class='num' style='width:220px; display:flex; align-items:center; gap:6px;'><span style='flex:none; font-weight:bold'>100.0%</span><div class='bar' style='flex:1;'><div class='bar-inner bar-errors' style='width:{MAX_WIDTH}px'></div></div></td><td class='num' style='font-weight:bold'>{occ_errors_fixed + occ_errors_skipped}</td><td class='num' style='width:220px; display:flex; align-items:center; gap:6px;'><span style='flex:none; font-weight:bold'>100.0%</span><div class='bar' style='flex:1;'><div class='bar-inner bar-errors' style='width:{MAX_WIDTH}px'></div></div></td></tr>")
    
    append(f"<tr><td class='warnings'>WARNINGS CORREGIDOS</td><td class='num'>{files_warnings_fixed}</td><td class='num' style='width:220px; display:flex; align-items:center; gap:6px;'><span style='flex:none'>{pct_files_warnings:.1f}%</span><div class='bar' style='flex:1;'><div class='bar-inner bar-warnings' style='width:{bar_files_warnings}px'></div></div></td><td class='num'>{occ_warnings_fixed}</td><td class='num' style='width:220px; display:flex; align-items:center; gap:6px;'><span style='flex:none'>{pct_occ_warnings:.1f}%</span><div class='bar' style='flex:1;'><div class='bar-inner bar-warnings' style='width:{bar_occ_warnings}px'></div></div></td></tr>")
    
    append(f"<tr><td class='warnings'>WARNINGS SALTADOS</td><td class='num'>{files_warnings_skipped}</td><td class='num' style='width:220px; display:flex; align-items:center; gap:6px;'><span style='flex:none'>{100.0 - pct_files_warnings:.1f}%</span><div class='bar' style='flex:1;'><div class='bar-inner bar-warnings' style='width:{MAX_WIDTH - bar_files_warnings}px'></div></div></td><td class='num'>{occ_warnings_skipped}</td><td class='num' style='width:220px; display:flex; align-items:center; gap:6px;'><span style='flex:none'>{100.0 - pct_occ_warnings:.1f}%</span><div class='bar' style='flex:1;'><div class='bar-inner bar-warnings' style='width:{MAX_WIDTH - bar_occ_warnings}px'></div></div></td></tr>")
    
    append(f"<tr><td class='warnings' style='font-weight:bold'>WARNINGS PROCESADOS</td><td class='num' style='font-weight:bold'>{files_warnings_total}</td><td class='num' style='width:220px; display:flex; align-items:center; gap:6px;'><span style='flex:none; font-weight:bold'>100.0%</span><div class='bar' style='flex:1;'><div class='bar-inner bar-warnings' style='width:{MAX_WIDTH}px'></div></div></td><td class='num' style='font-weight:bold'>{occ_warnings_fixed + occ_warnings_skipped}</td><td class='num' style='width:220px; display:flex; align-items:center; gap:6px;'><span style='flex:none; font-weight:bold'>100.0%</span><div class='bar' style='flex:1;'><div class='bar-inner bar-warnings' style='width:{MAX_WIDTH}px'></div></div></td></tr>")
    
    append(f"<tr style='background:#e3f2fd'><td class='total' style='color:#1976d2'>TOTAL CORREGIDOS</td><td class='num'>{total_files_fixed}</td><td class='num' style='width:220px; display:flex; align-items:center; gap:6px;'><span style='flex:none'>{pct_total_files:.1f}%</span><div class='bar' style='flex:1;'><div class='bar-inner' style='background:#42a5f5; width:{bar_total_files}px'></div></div></td><td class='num'>{total_occ_fixed}</td><td class='num' style='width:220px; display:flex; align-items:center; gap:6px;'><span style='flex:none'>{pct_total_occ:.1f}%</span><div class='bar' style='flex:1;'><div class='bar-inner' style='background:#42a5f5; width:{bar_total_occ}px'></div></div></td></tr>")
    
    append(f"<tr style='background:#e3f2fd'><td class='total' style='color:#1976d2'>TOTAL SALTADOS</td><td class='num' style='font-weight:bold'>{total_files - total_files_fixed}</td><td class='num' style='width:220px; display:flex; align-items:center; gap:6px;'><span style='flex:none; font-weight:bold'>{100.0 - pct_total_files:.1f}%</span><div class='bar' style='flex:1;'><div class='bar-inner' style='background:#bdbdbd; width:{MAX_WIDTH - bar_total_files}px'></div></div></td><td class='num'>{total_occ - total_occ_fixed}</td><td class='num' style='width:220px; display:flex; align-items:center; gap:6px;'><span style='flex:none'>{100.0 - pct_total_occ:.1f}%</span><div class='bar' style='flex:1;'><div class='bar-inner' style='background:#42a5f5; width:{MAX_WIDTH - bar_total_occ}px'></div></div></td></tr>")
    
    append(f"<tr style='background:#e3f2fd'><td class='total' style='color:#1976d2; font-weight:bold'>TOTAL</td><td class='num' style='font-weight:bold'>{total_files}</td><td class='num' style='width:220px; display:flex; align-items:center; gap:6px;'><span style='flex:none; font-weight:bold'>100.0%</span><div class='bar' style='flex:1;'><div class='bar-inner' style='background:#42a5f5; width:{MAX_WIDTH}px'></div></div></td><td class='num' style='font-weight:bold'>{total_occ}</td><td class='num' style='width:220px; display:flex; align-items:center; gap:6px;'><span style='flex:none; font-weight:bold'>100.0%</span><div class='bar' style='flex:1;'><div class='bar-inner' style='background:#42a5f5; width:{MAX_WIDTH}px'></div></div></td></tr>")
    
    append("</table>")
    append("<div style='margin: 15px 0; padding: 12px; background: #e3f2fd; border-left: 4px solid #2196F3; border-radius: 4px;'>")
    append("<strong>ℹ️ Nota:</strong> Algunos errores pueden corregirse indirectamente como efecto secundario de otras transformaciones. ")
    append("Por ejemplo, al transformar <code>simple_strtoul(str,NULL,0)</code> a <code>kstrtoul(str, NULL, 0)</code>, ")
    append("también se corrigen automáticamente los errores de espaciado alrededor de las comas. ")
    append("El contador de 'errores corregidos' refleja las correcciones directas aplicadas.")
    append("</div>")
    
    # ============================
    # RESUMEN POR MOTIVO - ERRORES
    # ============================
    error_fixes_by_reason = defaultdict(lambda: {'files': set(), 'lines': []})
    warning_fixes_by_reason = defaultdict(lambda: {'files': set(), 'lines': []})
    
    for filepath, issues in fixed_data.items():
        for error in issues.get('error', []):
            if error.get('fixed'):
                reason = error['message']
                error_fixes_by_reason[reason]['files'].add(filepath)
                error_fixes_by_reason[reason]['lines'].append(error['line'])
        
        for warning in issues.get('warning', []):
            if warning.get('fixed'):
                reason = warning['message']
                warning_fixes_by_reason[reason]['files'].add(filepath)
                warning_fixes_by_reason[reason]['lines'].append(warning['line'])
    
    if error_fixes_by_reason:
        append("<h3 class='errors'>Errores</h3>")
        append("<table>")
        append(f"<tr><th>Motivo</th><th>Ficheros</th><th style='width:220px;'>% Ficheros</th><th>Casos</th><th style='width:220px;'>% Errores</th></tr>")
        
        total_error_files = len(set(f for d in error_fixes_by_reason.values() for f in d['files']))
        total_error_cases = sum(len(d['lines']) for d in error_fixes_by_reason.values())
        
        import hashlib
        # Ordenar por número de casos descendente
        for reason in sorted(error_fixes_by_reason.keys(), key=lambda r: len(error_fixes_by_reason[r]['lines']), reverse=True):
            files_count = len(error_fixes_by_reason[reason]['files'])
            cases_count = len(error_fixes_by_reason[reason]['lines'])
            files_pct = (100.0 * files_count) / max(1, total_error_files)
            cases_pct = (100.0 * cases_count) / max(1, total_error_cases)
            
            # Usar mismo sistema que analyzer: id_HASH
            reason_id = hashlib.sha1(("ERROR:" + reason).encode()).hexdigest()[:12]
            
            # Remover prefijo ERROR: si existe
            display_reason = reason.replace("ERROR: ", "")
            
            append(f"<tr><td>{html_module.escape(display_reason)}</td><td class='num'>{files_count}</td>")
            append(f"<td class='num' style='width:220px; display:flex; align-items:center; gap:6px;'><span style='flex:none'>{files_pct:.1f}%</span>")
            append(f"<div class='bar' style='flex:1;'><div class='bar-inner bar-errors' style='width:{int(files_pct * 170 / 100)}px'></div></div></td>")
            append(f"<td class='num'><a href='autofix-detail-reason.html#id_{reason_id}'>{cases_count}</a></td><td class='num' style='width:220px; display:flex; align-items:center; gap:6px;'>")
            append(f"<span style='flex:none'>{cases_pct:.1f}%</span><div class='bar' style='flex:1;'><div class='bar-inner bar-errors' style='width:{int(cases_pct * 170 / 100)}px'></div></div></td></tr>")
        
        append("</table>")
    
    # ============================
    # RESUMEN POR MOTIVO - WARNINGS
    # ============================
    if warning_fixes_by_reason:
        append("<h3 class='warnings'>Warnings</h3>")
        append("<table>")
        append(f"<tr><th>Motivo</th><th>Ficheros</th><th style='width:220px;'>% Ficheros</th><th>Casos</th><th style='width:220px;'>% Warnings</th></tr>")
        
        total_warning_files = len(set(f for d in warning_fixes_by_reason.values() for f in d['files']))
        total_warning_cases = sum(len(d['lines']) for d in warning_fixes_by_reason.values())
        
        import hashlib
        # Ordenar por número de casos descendente
        for reason in sorted(warning_fixes_by_reason.keys(), key=lambda r: len(warning_fixes_by_reason[r]['lines']), reverse=True):
            files_count = len(warning_fixes_by_reason[reason]['files'])
            cases_count = len(warning_fixes_by_reason[reason]['lines'])
            files_pct = (100.0 * files_count) / max(1, total_warning_files)
            cases_pct = (100.0 * cases_count) / max(1, total_warning_cases)
            
            # Usar mismo sistema que analyzer: id_HASH
            reason_id = hashlib.sha1(("WARNING:" + reason).encode()).hexdigest()[:12]
            
            # Remover prefijo WARNING: si existe
            display_reason = reason.replace("WARNING: ", "")
            
            append(f"<tr><td>{html_module.escape(display_reason)}</td><td class='num'>{files_count}</td>")
            append(f"<td class='num' style='width:220px; display:flex; align-items:center; gap:6px;'><span style='flex:none'>{files_pct:.1f}%</span>")
            append(f"<div class='bar' style='flex:1;'><div class='bar-inner bar-warnings' style='width:{int(files_pct * 170 / 100)}px'></div></div></td>")
            append(f"<td class='num'><a href='autofix-detail-reason.html#id_{reason_id}'>{cases_count}</a></td><td class='num' style='width:220px; display:flex; align-items:center; gap:6px;'>")
            append(f"<span style='flex:none'>{cases_pct:.1f}%</span><div class='bar' style='flex:1;'><div class='bar-inner bar-warnings' style='width:{int(cases_pct * 170 / 100)}px'></div></div></td></tr>")
        
        append("</table>")
    
    append("</body></html>")
    
    with open(html_file, "w", encoding="utf-8") as f:
        f.write("\n".join(html_out))

def generate_autofix_detail_reason_html(fixed_data, html_file):
    """Genera autofix-detail-reason.html con detalles agrupados por tipo de fix"""
    
    fixed_by_reason = defaultdict(lambda: {'error': defaultdict(list), 'warning': defaultdict(list)})
    
    for filepath, issues in fixed_data.items():
        display_path = display_fp(filepath)
        for issue_type in ['error', 'warning']:
            for issue in issues.get(issue_type, []):
                if issue.get('fixed'):
                    reason = issue['message']
                    fixed_by_reason[reason][issue_type][filepath].append(issue['line'])
    
    html_out = []
    append = html_out.append
    timestamp = datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    
    append("<!doctype html><html><head><meta charset='utf-8'>")
    append("<style>")
    append(COMMON_CSS)
    append(".fix-type-count { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }")
    append(".fix-type-card { padding: 12px; border-radius: 6px; border-left: 4px solid; text-align: center; }")
    append(".fix-type-card.error { background: #ffebee; border-color: #d32f2f; }")
    append(".fix-type-card.warning { background: #fff3e0; border-color: #f57c00; }")
    append(".fix-type-card .type-name { font-size: 11px; color: #555; text-transform: uppercase; margin-bottom: 5px; }")
    append(".fix-type-card .count { font-size: 20px; font-weight: bold; }")
    append("</style></head><body>")
    append(f"<h1>Autofix - Detalle por motivo <span style='font-weight:normal'>{timestamp}</span></h1>")
    
    error_count = sum(len(fixed_by_reason[r]['error']) for r in fixed_by_reason)
    warning_count = sum(len(fixed_by_reason[r]['warning']) for r in fixed_by_reason)
    
    append("<div class='fix-type-count'>")
    append(f"<div class='fix-type-card error'><div class='type-name'>Tipos de Errores Fijados</div><div class='count'>{error_count}</div></div>")
    append(f"<div class='fix-type-card warning'><div class='type-name'>Tipos de Warnings Fijados</div><div class='count'>{warning_count}</div></div>")
    append(f"<div class='fix-type-card warning'><div class='type-name'>Total de Motivos Diferentes</div><div class='count'>{len(fixed_by_reason)}</div></div>")
    append("</div>")
    
    import hashlib
    for reason in sorted(fixed_by_reason.keys()):
        # Usar mismo sistema que analyzer: id_HASH
        is_error = bool(fixed_by_reason[reason]['error'])
        prefix = "ERROR:" if is_error else "WARNING:"
        reason_id = f"id_{hashlib.sha1((prefix + reason).encode()).hexdigest()[:12]}"
        css_class = 'errors' if is_error else 'warnings'
        
        append(f"<h4 id='{reason_id}' class='{css_class}'>{prefix} {html_module.escape(reason)}</h4>")
        
        for filepath in sorted(set(list(fixed_by_reason[reason]['error'].keys()) + list(fixed_by_reason[reason]['warning'].keys()))):
            display_path = display_fp(filepath)
            file_id = hashlib.sha1(filepath.encode()).hexdigest()[:8]
            lines = sorted(set(fixed_by_reason[reason]['error'].get(filepath, []) + fixed_by_reason[reason]['warning'].get(filepath, [])))
            
            append(f"<div style='margin-left: 20px; margin-bottom: 10px;'>")
            append(f"<strong><a href='autofix-detail-file.html#FILE:{file_id}' style='color:#2196F3;'>{display_path}</a></strong>")
            append(f"<div style='font-size:12px; color:#666;'> Líneas: {', '.join(map(str, lines))}</div>")
            append(f"</div>")
    
    append("</body></html>")
    
    with open(html_file, "w", encoding="utf-8") as f:
        f.write("\n".join(html_out))

def generate_autofix_detail_file_html(fixed_data, html_file, kernel_dir="."):
    """Genera autofix-detail-file.html con detalles expandibles por fichero"""
    
    html_out = []
    append = html_out.append
    timestamp = datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    
    # Helper para colorizar diffs
    def _escape_html(s):
        return html_module.escape(s)
    
    def _format_diff_html(diff_text):
        if not diff_text or not diff_text.strip():
            return '<pre class="diff-pre" style="color:#999;">No changes</pre>'
        out = ['<pre class="diff-pre">']
        for line in diff_text.split('\n'):
            if line.startswith('+++') or line.startswith('---'):
                out.append(f'<span style="color:#999; font-weight:bold;">{_escape_html(line)}</span>')
            elif line.startswith('@@'):
                out.append(f'<span style="color:#2196F3; font-weight:bold;">{_escape_html(line)}</span>')
            elif line.startswith('+') and not line.startswith('+++'):
                out.append(f'<span style="color:#4CAF50; background:#f1f8f4;">{_escape_html(line)}</span>')
            elif line.startswith('-') and not line.startswith('---'):
                out.append(f'<span style="color:#f44336; background:#ffe6e6;">{_escape_html(line)}</span>')
            else:
                out.append(_escape_html(line))
        out.append('</pre>')
        return '\n'.join(out)
    
    def _get_diff(bak_path, current_path):
        try:
            res = subprocess.run(['diff', '-u', bak_path, current_path], capture_output=True, text=True)
            return res.stdout
        except Exception:
            return ''
    
    append("<!doctype html><html><head><meta charset='utf-8'>")
    append("<style>")
    append(COMMON_CSS)
    append(".file-summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin: 20px 0; max-width: 100%; }")
    append(".file-summary-card { padding: 10px; border-radius: 4px; background: #f5f5f5; border: 1px solid #ddd; font-size: 12px; }")
    append(".file-summary-card .fname { font-weight: bold; color: #2196F3; margin-bottom: 5px; word-break: break-word; }")
    append(".file-summary-card .stats { display: flex; gap: 10px; justify-content: space-between; }")
    append(".file-summary-card .stat { display: flex; align-items: center; gap: 4px; }")
    append(".file-summary-card .fixed-s { color: #2e7d32; }")
    append(".file-summary-card .skipped-s { color: #757575; }")
    append("</style></head><body>")
    append(f"<h1>Autofix - Detalle por fichero <span style='font-weight:normal'>{timestamp}</span></h1>")
    
    # Calcular summary para ficheros con fixes
    file_summaries = []
    for filepath in sorted(fixed_data.keys()):
        issues = fixed_data[filepath]
        fixed_count = sum(1 for i in issues.get('error', []) + issues.get('warning', []) if i.get('fixed'))
        skipped_count = sum(1 for i in issues.get('error', []) + issues.get('warning', []) if not i.get('fixed'))
        if fixed_count > 0:
            file_summaries.append((filepath, fixed_count, skipped_count))
    
    if file_summaries:
        append("<div class='file-summary'>")
        for filepath, fixed_count, skipped_count in file_summaries:
            display_path = display_fp(filepath)
            import hashlib
            file_id = hashlib.sha1(filepath.encode()).hexdigest()[:8]
            append(f"<div class='file-summary-card'><div class='fname'><a href='#FILE:{file_id}' style='color:#2196F3;'>{display_path}</a></div>")
            append(f"<div class='stats'><span class='stat fixed-s'>✓ {fixed_count}</span><span class='stat skipped-s'>✗ {skipped_count}</span></div></div>")
        append("</div>")
    
    for filepath in sorted(fixed_data.keys()):
        issues = fixed_data[filepath]
        display_path = display_fp(filepath)
        
        fixed_count = sum(1 for i in issues.get('error', []) + issues.get('warning', []) if i.get('fixed'))
        skipped_count = sum(1 for i in issues.get('error', []) + issues.get('warning', []) if not i.get('fixed'))
        
        if fixed_count == 0:
            continue
        
        import hashlib
        file_id = hashlib.sha1(filepath.encode()).hexdigest()[:8]
        
        # Calcular stats del diff
        total_added = 0
        total_removed = 0
        bak_path = filepath + '.bak'
        diff_text = None
        if os.path.exists(bak_path):
            diff_text = _get_diff(bak_path, filepath)
            total_added = len([l for l in diff_text.split('\n') if l.startswith('+') and not l.startswith('+++')])
            total_removed = len([l for l in diff_text.split('\n') if l.startswith('-') and not l.startswith('---')])
        
        append(f"<details class='file-detail' id='FILE:{file_id}'>")
        append(f"<summary>")
        append(f"<span>{display_path}</span>")
        append(f"<div class='stats'>")
        append(f"<div class='stat-item'><span class='added'>+{total_added}</span> <span class='removed'>-{total_removed}</span></div>")
        append(f"<span class='fixed-badge'>{fixed_count} fixes</span>")
        if skipped_count > 0:
            append(f"<span class='skipped-badge'>{skipped_count} saltados</span>")
        append(f"</div>")
        append(f"</summary>")
        append(f"<div class='detail-content'>")
        
        # Mostrar diff coloreado si está disponible
        if diff_text:
            append(_format_diff_html(diff_text))
        else:
            # Fallback: mostrar detalles individuales sin diff
            for issue_type in ['error', 'warning']:
                for issue in sorted(issues.get(issue_type, []), key=lambda i: i['line']):
                    if issue.get('fixed'):
                        status = "<span class='fixed-badge'>FIXED</span>"
                    else:
                        status = "<span class='skipped-badge'>SKIPPED</span>"
                    
                    css_class = 'errors' if issue_type == 'error' else 'warnings'
                    append(f"<p><strong style='color:#2196F3;'>Línea {issue['line']}</strong> - {status}</p>")
                    append(f"<div style='font-size:12px; margin-left: 10px; margin-bottom: 10px;'><span class='{css_class}' style='display:inline-block; padding:4px 8px; border-radius:3px; background: #f5f5f5;'>{html_module.escape(issue['message'][:100])}</span></div>")
        
        append(f"</div>")
        append(f"</details>")
    
    append("<script>")
    append("document.addEventListener('DOMContentLoaded', () => {")
    append("  const hash = window.location.hash.substring(1);")
    append("  if (hash) {")
    append("    const elem = document.getElementById(hash);")
    append("    if (elem && elem.tagName === 'DETAILS') {")
    append("      elem.open = true;")
    append("      setTimeout(() => elem.scrollIntoView({ behavior: 'smooth' }), 100);")
    append("    }")
    append("  }")
    append("});")
    append("</script>")
    append("</body></html>")
    
    with open(html_file, "w", encoding="utf-8") as f:
        f.write("\n".join(html_out))


def generate_compile_html(results, html_file, kernel_root=None):
    """
    Genera reporte HTML para resultados de compilación.
    
    Args:
        results: Lista de CompilationResult
        html_file: Ruta del archivo HTML a generar
        kernel_root: Directorio raíz del kernel (para rutas relativas)
    """
    from pathlib import Path
    
    html_out = []
    append = html_out.append
    timestamp = datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    
    # Calcular estadísticas
    total = len(results)
    successful = sum(1 for r in results if r.success)
    failed = total - successful
    success_rate = (successful / total * 100) if total > 0 else 0
    total_duration = sum(r.duration for r in results)
    avg_duration = total_duration / total if total > 0 else 0
    
    # Header y CSS
    append("<!doctype html><html><head><meta charset='utf-8'>")
    append("<title>Compilation Report</title>")
    append("<style>")
    append(COMMON_CSS)
    append("""
    .success-box { 
        background: #e8f5e9; 
        border-left: 4px solid #4caf50; 
        padding: 15px; 
        margin: 10px 0; 
        border-radius: 4px; 
    }
    .failed-box { 
        background: #ffebee; 
        border-left: 4px solid #f44336; 
        padding: 15px; 
        margin: 10px 0; 
        border-radius: 4px; 
    }
    .stat-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 15px;
        margin: 20px 0;
    }
    .stat-card {
        background: #f9f9f9;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
    }
    .stat-card h3 {
        margin: 0 0 10px 0;
        font-size: 2em;
        color: #2196F3;
    }
    .stat-card.success h3 { color: #4caf50; }
    .stat-card.failed h3 { color: #f44336; }
    .stat-card p {
        margin: 0;
        color: #666;
        font-size: 0.9em;
    }
    .file-result {
        margin: 10px 0;
        border: 1px solid #ddd;
        border-radius: 4px;
        overflow: hidden;
    }
    .file-result summary {
        cursor: pointer;
        padding: 12px;
        background: #f9f9f9;
        font-weight: bold;
        display: flex;
        justify-content: space-between;
        align-items: center;
        user-select: none;
    }
    .file-result summary:hover { background: #f0f0f0; }
    .file-result.success summary { background: #e8f5e9; color: #2e7d32; }
    .file-result.failed summary { background: #ffebee; color: #c62828; }
    .file-result .detail-content {
        padding: 12px;
        background: white;
        border-top: 1px solid #ddd;
    }
    .error-output {
        background: #f5f5f5;
        padding: 10px;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
        font-size: 0.85em;
        overflow-x: auto;
        white-space: pre-wrap;
        border-left: 3px solid #f44336;
    }
    .breadcrumb {
        background: #f5f5f5;
        padding: 10px;
        border-radius: 4px;
        margin-bottom: 20px;
    }
    .breadcrumb a {
        color: #2196F3;
        text-decoration: none;
        margin: 0 5px;
    }
    .breadcrumb a:hover { text-decoration: underline; }
    </style>")
    append("</head><body>")
    
    # Breadcrumb
    append("<div class='breadcrumb'>")
    append("<a href='dashboard.html'>🏠 Dashboard</a> → ")
    append("<span>📦 Compilation Report</span>")
    append("</div>")
    
    # Header
    append(f"<h1>Informe de Compilación <span style='font-weight:normal'>{timestamp}</span></h1>")
    
    # Executive Summary con cajas de éxito
    append("<div class='stat-grid'>")
    
    append("<div class='stat-card'>")
    append(f"<h3>{total}</h3>")
    append("<p>Total Files</p>")
    append("</div>")
    
    append("<div class='stat-card success'>")
    append(f"<h3>{successful}</h3>")
    append("<p>Successful</p>")
    append("</div>")
    
    append("<div class='stat-card failed'>")
    append(f"<h3>{failed}</h3>")
    append("<p>Failed</p>")
    append("</div>")
    
    append("<div class='stat-card'>")
    append(f"<h3>{success_rate:.1f}%</h3>")
    append("<p>Success Rate</p>")
    append("</div>")
    
    append("<div class='stat-card'>")
    append(f"<h3>{total_duration:.1f}s</h3>")
    append("<p>Total Time</p>")
    append("</div>")
    
    append("<div class='stat-card'>")
    append(f"<h3>{avg_duration:.1f}s</h3>")
    append("<p>Avg Time</p>")
    append("</div>")
    
    append("</div>")
    
    # Resumen visual
    if failed == 0:
        append("<div class='success-box'>")
        append("<h3>✓ All files compiled successfully!</h3>")
        append(f"<p>All {total} files were compiled without errors.</p>")
        append("</div>")
    else:
        append("<div class='failed-box'>")
        append(f"<h3>⚠ {failed} file(s) failed to compile</h3>")
        append(f"<p>{successful} out of {total} files compiled successfully ({success_rate:.1f}%).</p>")
        append("</div>")
    
    # Resultados detallados
    append("<h2>Compilation Results</h2>")
    
    # Separar resultados exitosos y fallidos
    successful_results = [r for r in results if r.success]
    failed_results = [r for r in results if not r.success]
    
    # Mostrar fallidos primero
    if failed_results:
        append("<h3 class='errors'>Failed Compilations</h3>")
        for result in failed_results:
            file_name = Path(result.file_path).name
            rel_path = result.file_path
            if kernel_root:
                try:
                    rel_path = str(Path(result.file_path).relative_to(kernel_root))
                except ValueError:
                    pass
            
            append(f"<details class='file-result failed'>")
            append("<summary>")
            append(f"<span>✗ {html_module.escape(file_name)}</span>")
            append(f"<span style='font-size:0.9em;color:#666;'>{result.duration:.2f}s</span>")
            append("</summary>")
            append("<div class='detail-content'>")
            append(f"<p><strong>File:</strong> {html_module.escape(rel_path)}</p>")
            append(f"<p><strong>Duration:</strong> {result.duration:.2f}s</p>")
            
            if result.error_message:
                append("<p><strong>Error:</strong></p>")
                append(f"<div class='error-output'>{html_module.escape(result.error_message)}</div>")
            
            if result.stderr and result.stderr != result.error_message:
                append("<details style='margin-top:10px;'>")
                append("<summary style='cursor:pointer;color:#666;'>Full stderr output</summary>")
                append(f"<pre style='margin-top:10px;'>{html_module.escape(result.stderr[:2000])}</pre>")
                append("</details>")
            
            append("</div>")
            append("</details>")
    
    # Mostrar exitosos
    if successful_results:
        append("<h3 style='color:#2e7d32;'>Successful Compilations</h3>")
        for result in successful_results:
            file_name = Path(result.file_path).name
            rel_path = result.file_path
            if kernel_root:
                try:
                    rel_path = str(Path(result.file_path).relative_to(kernel_root))
                except ValueError:
                    pass
            
            append(f"<details class='file-result success'>")
            append("<summary>")
            append(f"<span>✓ {html_module.escape(file_name)}</span>")
            append(f"<span style='font-size:0.9em;color:#666;'>{result.duration:.2f}s</span>")
            append("</summary>")
            append("<div class='detail-content'>")
            append(f"<p><strong>File:</strong> {html_module.escape(rel_path)}</p>")
            append(f"<p><strong>Duration:</strong> {result.duration:.2f}s</p>")
            
            if result.stdout:
                append("<details style='margin-top:10px;'>")
                append("<summary style='cursor:pointer;color:#666;'>Compilation output</summary>")
                append(f"<pre style='margin-top:10px;'>{html_module.escape(result.stdout[:1000])}</pre>")
                append("</details>")
            
            append("</div>")
            append("</details>")
    
    append("</body></html>")
    
    # Escribir archivo
    Path(html_file).parent.mkdir(parents=True, exist_ok=True)
    with open(html_file, "w", encoding="utf-8") as f:
        f.write("\n".join(html_out))