# analyze_report.py
"""
Generación de reportes HTML para el analyzer
"""

import html as html_module
import datetime
from checkpatch_common import COMMON_CSS, percentage, bar_width


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
    
    html_out = []
    append = html_out.append
    timestamp = datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    
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
        f_bar = bar_width(f_count, total_files_count, max_width=PCT_CELL_WIDTH - 50)
        o_bar = bar_width(o_count, total_occ_count, max_width=PCT_CELL_WIDTH - 50)
        
        append(f"<tr><td class='{cls}'>{key.upper()}</td>"
               f"<td class='num'>{f_count}</td>"
               f"<td class='num' style='width:{PCT_CELL_WIDTH}px; display:flex; align-items:center; gap:6px;'>"
               f"<span style='flex:none'>{f_pct}</span>"
               f"<div class='bar'><div class='bar-inner bar-{cls}' style='width:{f_bar}px'></div></div>"
               f"</td>"
               f"<td class='num'>{o_count}</td>"
               f"<td class='num' style='width:{PCT_CELL_WIDTH}px; display:flex; align-items:center; gap:6px;'>"
               f"<span style='flex:none'>{o_pct}</span>"
               f"<div class='bar'><div class='bar-inner bar-{cls}' style='width:{o_bar}px'></div></div>"
               f"</td></tr>")
    
    append(f"<tr><td class='total'>TOTAL</td>"
           f"<td class='num'>{total_files_count}</td>"
           f"<td class='num' style='width:{PCT_CELL_WIDTH}px; display:flex; align-items:center; gap:6px;'>"
           f"<span style='flex:none'>100%</span>"
           f"<div class='bar'><div class='bar-inner bar-total' style='width:{PCT_CELL_WIDTH-50}px'></div></div>"
           f"</td>"
           f"<td class='num'>{total_occ_count}</td>"
           f"<td class='num' style='width:{PCT_CELL_WIDTH}px; display:flex; align-items:center; gap:6px;'>"
           f"<span style='flex:none'>100%</span>"
           f"<div class='bar'><div class='bar-inner bar-total' style='width:{PCT_CELL_WIDTH-50}px'></div></div>"
           f"</td></tr>")
    append("</table>")
    
    # ============================
    # RESUMEN POR MOTIVO - ERRORES
    # ============================
    if error_reasons:
        append("<h2>Resumen por Motivo - ERRORES</h2>")
        append("<table>")
        append("<tr><th>Motivo</th><th>Casos</th><th>Ficheros</th></tr>")
        for reason, count in sorted(error_reasons.items(), key=lambda x: -x[1]):
            files = error_reason_files.get(reason, [])
            append(f"<tr><td>{html_module.escape(reason)}</td>"
                   f"<td class='num'>{count}</td>"
                   f"<td><details><summary>{len(set(f[0] for f in files))} fichero(s)</summary><ul>")
            for file_path, line in files[:50]:  # Limitar a 50 para no sobrecargar
                append(f"<li>{html_module.escape(file_path)}:{line}</li>")
            if len(files) > 50:
                append(f"<li>... y {len(files) - 50} más</li>")
            append("</ul></details></td></tr>")
        append("</table>")
    
    # ============================
    # RESUMEN POR MOTIVO - WARNINGS
    # ============================
    if warning_reasons:
        append("<h2>Resumen por Motivo - WARNINGS</h2>")
        append("<table>")
        append("<tr><th>Motivo</th><th>Casos</th><th>Ficheros</th></tr>")
        for reason, count in sorted(warning_reasons.items(), key=lambda x: -x[1]):
            files = warning_reason_files.get(reason, [])
            append(f"<tr><td>{html_module.escape(reason)}</td>"
                   f"<td class='num'>{count}</td>"
                   f"<td><details><summary>{len(set(f[0] for f in files))} fichero(s)</summary><ul>")
            for file_path, line in files[:50]:
                append(f"<li>{html_module.escape(file_path)}:{line}</li>")
            if len(files) > 50:
                append(f"<li>... y {len(files) - 50} más</li>")
            append("</ul></details></td></tr>")
        append("</table>")
    
    # ============================
    # RESUMEN POR FUNCIONALIDAD
    # ============================
    append("<h2>Resumen por Funcionalidad</h2>")
    append("<table>")
    append("<tr><th>Funcionalidad</th><th>Correctos</th><th>Warnings</th><th>Errores</th></tr>")
    
    for func in sorted(summary.keys()):
        data = summary[func]
        correct_count = len(data["correct"])
        warning_count = len(data["warnings"])
        error_count = len(data["errors"])
        
        append(f"<tr><td>{html_module.escape(func)}</td>"
               f"<td class='num correct'>{correct_count}</td>"
               f"<td class='num warnings'>{warning_count}</td>"
               f"<td class='num errors'>{error_count}</td></tr>")
    
    append("</table>")
    
    append("</body></html>")
    
    # Escribir archivo
    with open(html_file, "w", encoding="utf-8") as f:
        f.write("\n".join(html_out))
