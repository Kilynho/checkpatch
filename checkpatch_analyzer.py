#!/usr/bin/env python3
"""
checkpatch_analyzer_pro_json.py

Analizador paralelo PRO de checkpatch.pl:
- Genera JSON compatible con autofix (solo ficheros con warnings/errores)
- HTML con tablero completo: resumen global, por motivo, por fichero
- Barra de progreso en terminal con listado de ficheros y estado
- Agrupa errores y warnings por motivos
- Compatible con posteriores correcciones automáticas
"""

import os
import html as html_module
import subprocess
from pathlib import Path
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import argparse
import time
import hashlib
import sys
import shutil
import json

# ============================
# Configuración por defecto
# ============================
EXTENSIONS = [".c", ".h"]
MAX_WORKERS = 4

FUNCTIONALITY_MAP = {
    "drivers": "Drivers",
    "fs": "Filesystems",
    "net": "Networking",
    "kernel": "Core Kernel",
    "arch": "Architecture",
    "lib": "Libraries",
    "include": "Headers",
}

# ============================
# Variables globales
# ============================
summary = defaultdict(lambda: {"correct": [], "warnings": [], "errors": []})
global_counts = {"correct": 0, "warnings": 0, "errors": 0}
error_reasons = Counter()
warning_reasons = Counter()
error_reason_files = defaultdict(list)
warning_reason_files = defaultdict(list)

lock = threading.Lock()
KERNEL_DIR = ""
CHECKPATCH = ""

total_files = 0
completed_files = 0
start_time = None
log_lines = []
printed_lines = 0

# ============================
# Funciones utilitarias
# ============================
def get_functionality(path):
    rel_path = os.path.relpath(path, KERNEL_DIR)
    parts = Path(rel_path).parts
    for part in parts:
        if part in FUNCTIONALITY_MAP:
            return FUNCTIONALITY_MAP[part]
    return "Otros"

def run_checkpatch(file_path):
    try:
        result = subprocess.run([CHECKPATCH, "--file", file_path],
                                capture_output=True, text=True, timeout=300)
        return result.stdout or ""
    except subprocess.TimeoutExpired:
        return "ERROR: checkpatch timeout\n"
    except Exception as e:
        return f"ERROR: exception running checkpatch: {e}\n"

import re

def extract_reasons(output):
    errors = []
    warnings = []
    last_pending = None

    for line in output.splitlines():
        s = line.strip()

        # Detecta línea tipo "#123: FILE: ..."
        m = re.match(r"#(\d+): FILE: .*", s)
        if m:
            line_number = int(m.group(1))

            # Asignar a último warning/error pendiente
            if last_pending is not None:
                last_pending["line"] = line_number
                last_pending = None

            continue

        # Detecta ERROR
        if s.startswith("ERROR:"):
            entry = {"message": s, "line": None}
            errors.append(entry)
            last_pending = entry
            continue

        # Detecta WARNING
        if s.startswith("WARNING:"):
            entry = {"message": s, "line": None}
            warnings.append(entry)
            last_pending = entry
            continue

    return errors, warnings


def safe_id(text):
    h = hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]
    return f"id_{h}"

# ============================
# HTML generator PRO
# ============================
def write_html():
    import datetime
    import os
    import html

    html_out = []
    append = html_out.append

    timestamp = datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")

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
    details { margin-bottom: 8px; }
    pre { background: #f4f4f4; padding: 8px; border-radius: 4px; overflow-x: auto; }
    .bar { display: inline-block; height: 12px; background: #ddd; border-radius: 3px; width: 100%; }
    .bar-inner { height: 100%; border-radius: 3px; }
    .bar-errors { background: #e57373; }
    .bar-warnings { background: #ffb74d; }
    .bar-correct { background: #81c784; }
    .bar-total { background: #2196F3; }
    th.num, td.num { text-align: center; width: 110px; }
           
/* Analyzer-style per-file detail styling (from autofix diffs generator) */
details.file-detail { margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; overflow: hidden; }
details.file-detail summary { cursor: pointer; padding: 12px; background: #f9f9f9; font-weight: bold; color: #2196F3; user-select: none; display: flex; justify-content: space-between; align-items: center; }
details.file-detail summary:hover { background: #f0f0f0; }
.detail-content { padding: 12px; background: white; }
.stats { display: flex; gap: 20px; align-items: center; margin-left: auto; }
.stat-item { display: flex; align-items: center; gap: 4px; }
.added { color: #ffb74d; font-weight: bold; }
.removed { color: #f44336; font-weight: bold; }
.fixed-badge { background: #4CAF50; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: normal; }
.diff-pre { background:#f5f5f5; padding:12px; border-radius:4px; overflow-x:auto; font-size:11px; line-height:1.4; border-left:3px solid #2196F3; }
""")
    append("</style></head><body>")
    append(f"<h1>Informe Checkpatch Analyzer <span style='font-weight:normal'>{timestamp}</span></h1>")

    # ============================
    #   RESUMEN GLOBAL
    # ============================

    total_files_count = sum(len(summary[func]["errors"]) +
                            len(summary[func]["warnings"]) +
                            len(summary[func]["correct"]) for func in summary)

    files_errors = sum(len(summary[func]["errors"]) for func in summary)
    files_warnings = sum(len(summary[func]["warnings"]) for func in summary)
    files_correct = sum(len(summary[func]["correct"]) for func in summary)

    occ_errors = sum(error_reasons.values())
    occ_warnings = sum(warning_reasons.values())
    occ_correct = sum(global_counts["correct"] for func in summary)

    total_occ_count = occ_errors + occ_warnings + occ_correct

    def pct(val, total):
        return f"{(val / total * 100):.1f}%" if total > 0 else "0%"

    def bar_width(val, total, max_width=200):
        return int(val / total * max_width) if total > 0 else 0

    PCT_CELL_WIDTH = 220

    append("<h2>Resumen global</h2>")
    append("<table>")
    append(f"<tr><th>Estado</th><th>Ficheros</th>"
           f"<th style='width:{PCT_CELL_WIDTH}px;'>% Ficheros</th>"
           f"<th>Casos</th>"
           f"<th style='width:{PCT_CELL_WIDTH}px;'>% Casos</th></tr>")

    for key, cls, f_count, o_count in [
        ("errors","errors", files_errors, occ_errors),
        ("warnings","warnings", files_warnings, occ_warnings),
        ("correct","correct", files_correct, occ_correct)
    ]:
        f_pct = pct(f_count, total_files_count)
        o_pct = pct(o_count, total_occ_count)
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
    #   RESUMEN POR MOTIVO
    # ============================

    def write_reason_table(title_cls, title_text, reasons_dict, reason_files_dict, bar_cls):
        total_reasons = sum(reasons_dict.values())
        if total_reasons == 0:
            append(f"<h3 class='{title_cls}'>{title_text}</h3><p>No se han detectado {title_text.lower()}.</p>")
            return

        append(f"<h3 class='{title_cls}'>{title_text}</h3>")
        append("<table>")
        append("<tr><th>Motivo</th><th>Ficheros</th><th>% Ficheros</th>"
               "<th>Casos</th><th>% Casos</th></tr>")

        all_files = set()
        for fp_list in reason_files_dict.values():
            for fp, _ in fp_list:
                all_files.add(fp)
        total_files_with_status = len(all_files)

        for reason, cnt in reasons_dict.most_common():
            files_for_reason = {fp for fp, _ in reason_files_dict[reason]}
            num_files = len(files_for_reason)

            pct_files = pct(num_files, total_files_with_status)
            pct_cases = pct(cnt, total_reasons)

            bar_files = bar_width(num_files, total_files_with_status, max_width=PCT_CELL_WIDTH - 50)
            bar_cases = bar_width(cnt, total_reasons, max_width=PCT_CELL_WIDTH - 50)

            rid = safe_id(title_text.upper() + ":" + reason)

            append("<tr>"
                   f"<td>{html.escape(reason)}</td>"
                   f"<td class='num'>{num_files}</td>"
                   f"<td class='num' style='width:{PCT_CELL_WIDTH}px; display:flex; align-items:center; gap:6px;'>"
                   f"<span style='flex:none'>{pct_files}</span>"
                   f"<div class='bar'><div class='bar-inner bar-{bar_cls}' style='width:{bar_files}px'></div></div>"
                   "</td>"
                   f"<td class='num'><a href='#{rid}'>{cnt}</a></td>"
                   f"<td class='num' style='width:{PCT_CELL_WIDTH}px; display:flex; align-items:center; gap:6px;'>"
                   f"<span style='flex:none'>{pct_cases}</span>"
                   f"<div class='bar'><div class='bar-inner bar-{bar_cls}' style='width:{bar_cases}px'></div></div>"
                   "</td></tr>")

        append("</table>")

    write_reason_table("errors", "Errores", error_reasons, error_reason_files, "errors")
    write_reason_table("warnings", "Warnings", warning_reasons, warning_reason_files, "warnings")

    # ============================
    #   DETALLE POR MOTIVO
    # ============================

    append("<h2>Detalle por motivo</h2>")

    def write_reason_detail(title_cls, title_text, reasons_dict, reason_files_dict):
        for reason, cnt in reasons_dict.most_common():
            rid = safe_id(title_text.upper() + ":" + reason)  # <-- usar title_text.upper() igual que en la tabla
            append(f"<h4 id='{rid}' class='{title_cls}'>{html.escape(reason)} — {cnt} casos</h4><ul>")
            file_counts = {}
            for fp, _ in reason_files_dict[reason]:
                file_counts[fp] = file_counts.get(fp, 0) + 1
            for fp, impacts in file_counts.items():
                rp = os.path.relpath(fp, KERNEL_DIR)
                file_rid = safe_id(fp)
                append(f"<li><a href='#{file_rid}'>{rp} ({impacts})</a></li>")
            append("</ul>")

    write_reason_detail("errors", "Errores", error_reasons, error_reason_files)
    write_reason_detail("warnings", "Warnings", warning_reasons, warning_reason_files)

    # ============================
    #   DETALLE POR FICHERO
    # ============================
    def _escape_html(s):
            return html_module.escape(s)
    
    def _format_diff_html(diff_text):
            if not diff_text or not diff_text.strip():
                return '<pre class="diff-pre" style="color:#999;">No changes</pre>'
            out = ['<pre class="diff-pre">']
            for line in diff_text.split('\n'):
                if line.startswith('#'):
                    out.append(f'<span style="color:#999; font-weight:bold;">{_escape_html(line)}</span>')
                elif line.startswith('+'):
                    out.append(f'<span style="color:#4CAF50; background:#f1f8f4;">{_escape_html(line)}</span>')
                elif line.startswith('WARNING'):
                    out.append(f'<span style="color:#73400D; background:#FAE6D1;">{_escape_html(line)}</span>')
                elif line.startswith('ERROR'):
                    out.append(f'<span style="color:#f44336; background:#ffe6e6;">{_escape_html(line)}</span>')
                else:
                    out.append(_escape_html(line))
            out.append('</pre>')
            return '\n'.join(out)
    
    append("<h2>Detalle por fichero</h2>")
    # Recopilar todos los ficheros con sus impactos y ordenar por total descendente
    all_files = []
    for status in ["errors", "warnings", "correct"]:
        for func, results in summary.items():
            for file_path, output in results[status]:
                total_warnings = output.count("WARNING:")
                total_error = output.count("ERROR:")
                total_impacts = total_warnings + total_error
                all_files.append({
                    "path": file_path,
                    "output": output,
                    "warnings": total_warnings,
                    "errors": total_error,
                    "total": total_impacts
                })
    
    # Ordenar por total de impactos descendente
    all_files.sort(key=lambda x: x["total"], reverse=True)
    
    # Mostrar todos los ficheros
    for file_info in all_files:
        rp = os.path.relpath(file_info["path"], KERNEL_DIR)
        fid = safe_id(file_info["path"])
        total_warnings = file_info["warnings"]
        total_error = file_info["errors"]
        total_impacts = file_info["total"]
        
        append(f"<details class='file-detail' id='{fid}'><summary>{rp}"
        f"<div class='stats'><div class='stat-item'><span class='added'>+{total_warnings}</span> <span class='removed'>+{total_error}</span></div>"
        f"<span class='fixed-badge'>{total_impacts} total</span></div></summary>")
        # show combined diff if available
        if file_info["output"]:
            append("<div class='detail-content'>")
            append(_format_diff_html(html_module.escape(file_info["output"])))
            append("</div>")
        append("</details>")
    append("</body></html>")

    # Ensure output directory exists and write HTML into the `html/` subdirectory
    os.makedirs("html", exist_ok=True)
    out_path = os.path.join("html", "analyzer.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(html_out))

# ============================
# Barra de progreso en terminal
# ============================
def redraw_screen(progress_done, progress_total):
    global printed_lines
    if printed_lines > 0:
        sys.stdout.write(f"\x1b[{printed_lines}F")  # move cursor up
    sys.stdout.write("\x1b[0J")  # clear from cursor down
    for line in log_lines:
        sys.stdout.write(line + "\n")
    percent = (progress_done / progress_total) * 100 if progress_total else 0
    bar_len = shutil.get_terminal_size().columns - 40
    filled = int(bar_len * progress_done / progress_total) if progress_total else 0
    bar = "#" * filled + "-" * (bar_len - filled)
    sys.stdout.write(f"[ANALYZER] Progreso: [{bar}] {percent:5.1f}% ({progress_done}/{progress_total})\n")
    printed_lines = len(log_lines) + 1
    sys.stdout.flush()

# ============================
# Worker
# ============================
def process_file(file_path):
    global completed_files
    output = run_checkpatch(file_path)
    errors, warnings = extract_reasons(output)
    status = "errors" if errors else "warnings" if warnings else "correct"
    func = get_functionality(file_path)

    file_json = {"file": file_path, "warning": [], "error": []}

    # --- FIX mínimo: insertar la línea real en lugar de None ---
    for e in errors:
        file_json["error"].append({"message": e["message"], "line": e["line"]})
    for w in warnings:
        file_json["warning"].append({"message": w["message"], "line": w["line"]})
    # -----------------------------------------------------------

    with lock:
        summary[func][status].append((file_path, output))
        global_counts[status] += 1

        # Procesar errores
        for er in errors:
            msg = er["message"]  # clave para Counter y diccionario
            error_reasons[msg] += 1
            error_reason_files[msg].append((file_path, er))  # guardamos dict completo

        # Procesar warnings
        for wr in warnings:
            msg = wr["message"]
            warning_reasons[msg] += 1
            warning_reason_files[msg].append((file_path, wr))

        completed_files += 1
        log_lines.append(f"[ANALYZER] {os.path.relpath(file_path, KERNEL_DIR)}")
        write_html()
        redraw_screen(completed_files, total_files)

    return file_json

# ============================
# Main
# ============================
def collect_files(kernel_dir, paths):
    files = []
    seen = set()
    for p in paths:
        base = os.path.join(kernel_dir, p)
        if not os.path.exists(base):
            continue

        # Si es fichero, úsalo directamente si la extensión es válida
        if os.path.isfile(base):
            if any(base.endswith(ext) for ext in EXTENSIONS) and base not in seen:
                files.append(base)
                seen.add(base)
            continue

        # Si es carpeta, recorrer recursivamente
        for root, _, filenames in os.walk(base):
            for fn in filenames:
                if any(fn.endswith(ext) for ext in EXTENSIONS):
                    full = os.path.join(root, fn)
                    if full not in seen:
                        files.append(full)
                        seen.add(full)
    return files

def main():
    global KERNEL_DIR, CHECKPATCH, total_files, start_time

    parser = argparse.ArgumentParser(description="Analizador paralelo PRO de checkpatch con HTML/JSON")
    parser.add_argument("kernel_dir", help="Ruta a la carpeta del kernel")
    parser.add_argument("--paths", nargs="*", default=["."], help="Carpetas a analizar")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS, help="Número de hilos")
    parser.add_argument("--json", default="json/checkpatch.json", help="Archivo JSON de salida")
    args = parser.parse_args()

    KERNEL_DIR = os.path.abspath(args.kernel_dir)
    CHECKPATCH = os.path.join(KERNEL_DIR, "scripts", "checkpatch.pl")
    if not os.path.isfile(CHECKPATCH):
        print(f"ERROR: no se encuentra checkpatch.pl en: {CHECKPATCH}")
        return

    file_list = collect_files(KERNEL_DIR, args.paths)
    total_files = len(file_list)
    if total_files == 0:
        print("No se encontraron archivos para analizar.")
        return

    print(f"[ANALYZER] Archivos a analizar: {total_files}")
    start_time = time.time()
    write_html()  # HTML inicial

    files_json = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(process_file, f) for f in file_list]
        for f in as_completed(futures):
            file_entry = f.result()
            if file_entry["warning"] or file_entry["error"]:
                files_json.append(file_entry)

    # Guardar JSON limpio
    with open(args.json, "w", encoding="utf-8") as jf:
        json.dump(files_json, jf, indent=2)

    write_html()
    # Totales por motivo (ocurrencias), no por fichero
    occ_errors = sum(error_reasons.values())
    occ_warnings = sum(warning_reasons.values())
    occ_total = occ_errors + occ_warnings
    print(f"[ANALYZER] Errores encontrados: {occ_errors}")
    print(f"[ANALYZER] Warnings encontrados: {occ_warnings}")
    print(f"[ANALYZER] Total encontrados: {occ_total}")
    print(f"[ANALYZER] ✔ Análisis terminado.")
    print(f"[ANALYZER] ✔ Informe HTML generado: html/analyzer.html")
    print(f"[ANALYZER] ✔ JSON generado: {args.json}")

if __name__ == "__main__":
    main()
