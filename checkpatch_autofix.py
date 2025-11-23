#!/usr/bin/env python3
"""
Autofix extendido para checkpatch — versión modular
Ahora usa:

- fix_constants.py
- fix_utils.py
- fixes_core.py
- fix_report.py
- fix_main.py

Toda la lógica de autofixes está en fix_main.py (apply_fixes)
"""

import json
import argparse
from pathlib import Path

# ---- Módulo principal que aplica fixes ----
from fix_main import apply_fixes

# ---- Reporte HTML / Consola ----
from fix_report import generate_html_report, summarize_results


def main():
    parser = argparse.ArgumentParser(description="Autofix extendido checkpatch (modular)")
    parser.add_argument("json_input", help="JSON de entrada de checkpatch")
    parser.add_argument("--type", choices=["warning", "error", "all"], default="all",
                        help="Filtrar por tipo")
    parser.add_argument("--html", default="html/autofix.html", help="Archivo HTML de salida")
    parser.add_argument("--json-out", default="json/fixed.json", help="Archivo JSON de salida")
    parser.add_argument("--file", help="Procesar solo este fichero específico")
    args = parser.parse_args()

    json_file = Path(args.json_input)
    if not json_file.exists():
        print(f"[ERROR] No existe el archivo: {json_file}")
        return

    with open(json_file, "r") as f:
        files_data = json.load(f)

    # Estructura para report_data compatible con HTML
    from collections import defaultdict
    report_data = defaultdict(lambda: {"warning": [], "error": []})
    modified_files = set()
    errors_fixed = errors_skipped = warnings_fixed = warnings_skipped = 0

    file_filter = Path(args.file).resolve() if args.file else None

    for entry in files_data:
        file_path = Path(entry["file"]).resolve()

        if file_filter and file_filter != file_path:
            continue

        # Reunir issues según tipo
        issues_to_fix = []
        if args.type in ("warning", "all"):
            for w in entry.get("warning", []):
                issues_to_fix.append({"type": "warning", **w})
        if args.type in ("error", "all"):
            for e in entry.get("error", []):
                issues_to_fix.append({"type": "error", **e})

        issues_to_fix.sort(key=lambda x: -x["line"])  # de abajo hacia arriba

        # Aplicar fixes
        fix_results = apply_fixes(file_path, issues_to_fix)

        file_modified = False
        for orig_issue, res in zip(issues_to_fix, fix_results):
            typ = orig_issue["type"]
            line = orig_issue["line"]
            message = orig_issue["message"]

            fixed = res.get("fixed", False)

            report_data[str(file_path)][typ].append({
                "line": line,
                "message": message,
                "fixed": fixed
            })

            if fixed:
                file_modified = True
                if typ == "error":
                    errors_fixed += 1
                else:
                    warnings_fixed += 1
            else:
                if typ == "error":
                    errors_skipped += 1
                else:
                    warnings_skipped += 1

        if file_modified:
            modified_files.add(str(file_path))

    # Guardar JSON
    with open(args.json_out, "w") as jf:
        json.dump(report_data, jf, indent=2)

    # Generar HTML
    generate_html_report(report_data, args.html)

    # Resumen en consola
    summarize_results(report_data, args.json_out, args.html)

if __name__ == "__main__":
    main()
