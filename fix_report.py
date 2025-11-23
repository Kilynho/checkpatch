# fix_report.py
"""
Funciones para generación de reportes HTML
"""

import os
import html as html_module
from collections import defaultdict
import datetime
import subprocess

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

    def pct(val, total):
        return f"{(val / total * 100):.1f}%" if total else "0%"

    def bar_width(val, total, max_width=200):
        return int(val / total * max_width) if total else 0

    PCT_CELL_WIDTH = 220

    html_out = []
    append = html_out.append
    timestamp = datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")

    # --- Header y CSS ---
    append("<!doctype html><html><head><meta charset='utf-8'>")
    append("<style>")
    append("""
body { font-family: Arial, Helvetica, sans-serif; padding: 20px; }
h1 { display:flex; justify-content:space-between; align-items:center; }
table { border-collapse: collapse; margin-bottom: 20px; width: 100%; }
th, td { border: 1px solid #ccc; padding: 6px 10px; text-align: left; width: 100%; }
th { background: #eee; }
.correct { color: green; font-weight: bold; }
.warnings { color: orange; font-weight: bold; }
.errors { color: red; font-weight: bold; }
.total { font-weight: bold; color: #2196F3; }
h3.errors, h4.errors { color: #d32f2f; background: #ffebee; padding: 10px; border-left: 4px solid #d32f2f; border-radius: 4px; }
h3.warnings, h4.warnings { color: #f57c00; background: #fff3e0; padding: 10px; border-left: 4px solid #f57c00; border-radius: 4px; }
details { margin-bottom: 8px; }
pre { background: #f4f4f4; padding: 8px; border-radius: 4px; overflow-x: auto; white-space: pre-wrap; }
.bar { display: inline-block; height: 12px; background: #ddd; border-radius: 3px; }
.bar-inner { height: 100%; border-radius: 3px; }
.bar-errors { background: #e57373; }
.bar-warnings { background: #ffb74d; }
.bar-total { background: #2196F3; }
.skipped { color: #757575; font-weight: bold; }
th.num, td.num { text-align: center; width: 110px; }

/* Analyzer-style per-file detail styling (from autofix diffs generator) */
details.file-detail { margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; overflow: hidden; }
details.file-detail summary { cursor: pointer; padding: 12px; background: #f9f9f9; font-weight: bold; color: #2196F3; user-select: none; display: flex; justify-content: space-between; align-items: center; }
details.file-detail summary:hover { background: #f0f0f0; }
.detail-content { padding: 12px; background: white; }
.stats { display: flex; gap: 20px; align-items: center; margin-left: auto; }
.stat-item { display: flex; align-items: center; gap: 4px; }
.added { color: #4CAF50; font-weight: bold; }
.removed { color: #f44336; font-weight: bold; }
.fixed-badge { background: #4CAF50; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: normal; }
.diff-pre { background:#f5f5f5; padding:12px; border-radius:4px; overflow-x:auto; font-size:11px; line-height:1.4; border-left:3px solid #2196F3; }
""")
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
    f_pct = pct(f_count, f_count_errors_total)
    o_pct = pct(o_count, o_count_errors_total)
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
    f_pct = pct(f_count, f_count_errors_total)
    o_pct = pct(o_count, o_count_errors_total)
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
    f_pct = pct(f_count, f_count_warnings_total)
    o_pct = pct(o_count, o_count_warnings_total)
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
    f_pct = pct(f_count, f_count_warnings_total)
    o_pct = pct(o_count, o_count_warnings_total)
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
    f_pct = pct(f_count_corrected, total_files_all)
    o_pct = pct(o_count_corrected, total_occ_all)
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
    f_pct = pct(f_count_skipped, total_files_all)
    o_pct = pct(o_count_skipped, total_occ_all)
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
            pct_files = pct(count_files, total_files)
            pct_cases = pct(count_cases, total_cases)
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
    