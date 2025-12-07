#!/usr/bin/env python3
"""
main.py - Punto de entrada unificado

Modos de operación:
  --analyze: Analiza archivos con checkpatch.pl y genera reporte HTML
  --fix: Aplica correcciones automáticas a warnings/errores
  
Compatible con el flujo anterior de checkpatch_analyzer.py y checkpatch_autofix.py
"""

import argparse
import json
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Módulos unificados
from engine import (
    apply_fixes,
    analyze_file, 
    get_analysis_summary, 
    reset_analysis
)
from report import (
    generate_html_report, 
    summarize_results,
    generate_analyzer_html,
    generate_detail_reason_html,
    generate_detail_file_html,
    generate_dashboard_html,
    generate_autofix_html,
    generate_autofix_detail_reason_html,
    generate_autofix_detail_file_html,
    generate_compile_html
)
from utils import find_source_files
from compile import (
    compile_modified_files,
    restore_backups,
    print_summary,
    save_json_report
)


def analyze_mode(args):
    """Modo análisis: analiza archivos y genera reporte HTML."""
    
    # Buscar archivos en todos los directorios especificados
    all_files = []
    for source_dir in args.source_dirs:
        files = find_source_files(source_dir, extensions=args.extensions)
        all_files.extend(files)
    
    if not all_files:
        print(f"[ERROR] No se encontraron archivos con extensiones {args.extensions}")
        return 1
    
    checkpatch_script = args.checkpatch
    kernel_root = args.kernel_root
    
    # Resetear estructuras globales
    reset_analysis()
    
    # Estructura para JSON compatible con autofix
    json_data = []
    
    # Barra de progreso
    total = len(all_files)
    completed = 0
    lock = threading.Lock()
    
    def progress_bar(current, total):
        percent = current / total * 100
        bar_len = 40
        filled = int(bar_len * current / total)
        bar = '#' * filled + ' ' * (bar_len - filled)
        return f"[{bar}] {percent:.1f}% ({current}/{total})"
    
    print(f"[ANALYZER] Analizando {total} archivos con {args.workers} workers...")
    
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(analyze_file, f, checkpatch_script, kernel_root): f for f in all_files}
        
        for future in as_completed(futures):
            file_path = futures[future]
            try:
                errors, warnings, is_correct = future.result()
                
                # Agregar a JSON si tiene issues
                if errors or warnings:
                    json_data.append({
                        "file": str(file_path),
                        "error": errors,
                        "warning": warnings
                    })
                
                # Progreso
                with lock:
                    completed += 1
                    if completed % 10 == 0 or completed == total:
                        print(f"\r[ANALYZER] Progreso: {progress_bar(completed, total)}", end="")
                
            except Exception as e:
                print(f"\n[ERROR] {file_path}: {e}")
    
    print()  # Nueva línea después de la barra
    
    # Obtener resumen
    analysis_data = get_analysis_summary()
    
    # Generar HTML
    html_path = Path(args.html)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    generate_analyzer_html(analysis_data, html_path)
    
    # Generar HTMLs de detalle
    detail_reason_path = html_path.parent / "detail-reason.html"
    detail_file_path = html_path.parent / "detail-file.html"
    generate_detail_reason_html(analysis_data, detail_reason_path)
    generate_detail_file_html(analysis_data, detail_file_path)
    
    # Generar dashboard
    dashboard_path = html_path.parent / "dashboard.html"
    generate_dashboard_html(dashboard_path)
    
    # Generar JSON
    json_path = Path(args.json_out)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)
    
    # Resumen en consola
    gc = analysis_data["global_counts"]
    error_count = sum(analysis_data["error_reasons"].values())
    warning_count = sum(analysis_data["warning_reasons"].values())
    
    print(f"[ANALYZER] Errores encontrados: {error_count}")
    print(f"[ANALYZER] Warnings encontrados: {warning_count}")
    print(f"[ANALYZER] Total encontrados: {error_count + warning_count}")
    print(f"[ANALYZER] ✔ Análisis terminado.")
    print(f"[ANALYZER] ✔ Informe HTML generado: {html_path}")
    print(f"[ANALYZER] ✔ JSON generado: {json_path}")
    
    return 0


def fix_mode(args):
    """Modo autofix: aplica correcciones automáticas."""
    
    json_file = Path(args.json_input)
    if not json_file.exists():
        print(f"[ERROR] No existe el archivo: {json_file}")
        return 1
    
    with open(json_file, "r") as f:
        files_data = json.load(f)
    
    # Estructura para report_data
    from collections import defaultdict
    report_data = defaultdict(lambda: {"warning": [], "error": []})
    modified_files = set()
    
    file_filter = Path(args.file).resolve() if args.file else None
    
    print("[AUTOFIX] Procesando archivos...")
    
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
        
        if not issues_to_fix:
            continue
        
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
        
        if file_modified:
            modified_files.add(str(file_path))
            print(f"[AUTOFIX]  - {file_path.relative_to(file_path.parent.parent.parent)}")
    
    # Calcular estadísticas para resumen
    errors_fixed = sum(1 for issues in report_data.values() for i in issues.get("error", []) if i.get("fixed"))
    warnings_fixed = sum(1 for issues in report_data.values() for i in issues.get("warning", []) if i.get("fixed"))
    errors_skipped = sum(1 for issues in report_data.values() for i in issues.get("error", []) if not i.get("fixed"))
    warnings_skipped = sum(1 for issues in report_data.values() for i in issues.get("warning", []) if not i.get("fixed"))
    
    # Resumen en consola
    if errors_fixed + errors_skipped > 0:
        print(f"[AUTOFIX] Errores procesados: {errors_fixed + errors_skipped}")
        print(f"[AUTOFIX]  - Corregidos: {errors_fixed} ({100*errors_fixed/(errors_fixed+errors_skipped):.1f}%)")
        print(f"[AUTOFIX]  - Saltados : {errors_skipped} ({100*errors_skipped/(errors_fixed+errors_skipped):.1f}%)")
    
    if warnings_fixed + warnings_skipped > 0:
        print(f"[AUTOFIX] Warnings procesados: {warnings_fixed + warnings_skipped}")
        print(f"[AUTOFIX]  - Corregidos: {warnings_fixed} ({100*warnings_fixed/(warnings_fixed+warnings_skipped):.1f}%)")
        print(f"[AUTOFIX]  - Saltados : {warnings_skipped} ({100*warnings_skipped/(warnings_fixed+warnings_skipped):.1f}%)")
    
    total = errors_fixed + warnings_fixed + errors_skipped + warnings_skipped
    total_fixed = errors_fixed + warnings_fixed
    if total > 0:
        print(f"[AUTOFIX] Total procesados: {total}")
        print(f"[AUTOFIX]  - Corregidos: {total_fixed} ({100*total_fixed/total:.1f}%)")
        print(f"[AUTOFIX]  - Saltados : {total - total_fixed} ({100*(total-total_fixed)/total:.1f}%)")
    
    # Generar HTML
    html_path = Path(args.html)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generar 3 archivos de autofix
    generate_autofix_html(report_data, html_path)
    generate_autofix_detail_reason_html(report_data, html_path.parent / "autofix-detail-reason.html")
    generate_autofix_detail_file_html(report_data, html_path.parent / "autofix-detail-file.html")
    
    # Generar dashboard
    dashboard_path = html_path.parent / "dashboard.html"
    generate_dashboard_html(dashboard_path)
    
    # Guardar JSON de resultados
    json_out_path = Path(args.json_out)
    json_out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_out_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, default=str)
    
    print(f"[AUTOFIX] ✔ Análisis terminado {json_out_path}")
    print(f"[AUTOFIX] ✔ Informe HTML generado : {html_path}")
    print(f"[AUTOFIX] ✔ JSON generado: {json_out_path}")
    
    return 0


def compile_mode(args):
    """Modo compilación: compila archivos modificados y verifica que compilen."""
    
    json_file = Path(args.json_input)
    if not json_file.exists():
        print(f"[ERROR] No existe el archivo: {json_file}")
        return 1
    
    # Leer archivos modificados del JSON de autofix
    with open(json_file, "r") as f:
        report_data = json.load(f)
    
    # Extraer lista de archivos que fueron modificados
    modified_files = []
    if isinstance(report_data, dict):
        # JSON de autofix (formato: {file: {error: [], warning: []}})
        for file_path, issues in report_data.items():
            if file_path == "summary":
                continue
            # Verificar si hay algún fix aplicado
            has_fixes = any(
                i.get("fixed", False) 
                for issue_list in [issues.get("error", []), issues.get("warning", [])]
                for i in issue_list
            )
            if has_fixes:
                modified_files.append(Path(file_path))
    elif isinstance(report_data, list):
        # JSON de checkpatch (formato: [{file: ..., error: [], warning: []}])
        modified_files = [Path(entry["file"]) for entry in report_data]
    
    if not modified_files:
        print("[COMPILE] No se encontraron archivos modificados para compilar")
        return 0
    
    # Restaurar backups si se solicita
    if args.restore_before:
        print(f"[COMPILE] Restaurando {len(modified_files)} archivos desde backup...")
        restore_backups(modified_files)
    
    # Compilar archivos
    kernel_root = Path(args.kernel_root).resolve()
    if not kernel_root.exists():
        print(f"[ERROR] Kernel root no encontrado: {kernel_root}")
        return 1
    
    print(f"[COMPILE] Kernel root: {kernel_root}")
    results = compile_modified_files(
        modified_files, 
        kernel_root, 
        cleanup=not args.no_cleanup
    )
    
    # Restaurar backups después si se solicita
    if args.restore_after:
        print(f"\n[COMPILE] Restaurando {len(modified_files)} archivos desde backup...")
        restore_backups(modified_files)
    
    # Generar reportes
    html_path = Path(args.html)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    generate_compile_html(results, html_path, kernel_root)
    
    # Generar JSON
    json_path = Path(args.json_out)
    save_json_report(results, json_path)
    
    # Resumen en consola
    print_summary(results)
    
    print(f"\n[COMPILE] ✓ Informe HTML generado: {html_path}")
    print(f"[COMPILE] ✓ JSON generado: {json_path}")
    
    # Retornar 0 si todos compilaron exitosamente, 1 si hubo fallos
    failed_count = sum(1 for r in results if not r.success)
    return 1 if failed_count > 0 else 0


def main():
    parser = argparse.ArgumentParser(
        description="Checkpatch analyzer y autofix unificado",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Analizar archivos (estilo original)
  %(prog)s --analyze /path/to/kernel/linux --paths init
  
  # Aplicar fixes
  %(prog)s --fix --json-input json/checkpatch.json
  
  # Compilar archivos modificados
  %(prog)s --compile --json-input json/fixed.json --kernel-root /path/to/kernel/linux
        """
    )
    
    # Modo de operación
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--analyze", metavar="KERNEL_ROOT", 
                           help="Modo análisis: ruta al root del kernel Linux")
    mode_group.add_argument("--fix", action="store_true", help="Modo autofix")
    mode_group.add_argument("--compile", action="store_true", help="Modo compilación: prueba compilar archivos modificados")
    
    # Argumentos para análisis
    analyze_group = parser.add_argument_group("Opciones de análisis")
    analyze_group.add_argument("--paths", nargs="+", 
                              help="Subdirectorios a analizar (ej: init, kernel). Si se omite, analiza todo")
    analyze_group.add_argument("--extensions", nargs="+", default=[".c", ".h"],
                              help="Extensiones de archivo (default: .c .h)")
    analyze_group.add_argument("--workers", type=int, default=4,
                              help="Número de workers paralelos (default: 4)")
    
    # Argumentos para autofix
    fix_group = parser.add_argument_group("Opciones de autofix")
    fix_group.add_argument("--json-input", help="JSON de entrada de checkpatch o autofix")
    fix_group.add_argument("--type", choices=["warning", "error", "all"], default="all",
                          help="Filtrar por tipo (default: all)")
    fix_group.add_argument("--file", help="Procesar solo este fichero específico")
    
    # Argumentos para compilación
    compile_group = parser.add_argument_group("Opciones de compilación")
    compile_group.add_argument("--kernel-root", help="Directorio raíz del kernel Linux")
    compile_group.add_argument("--restore-before", action="store_true",
                              help="Restaurar backups antes de compilar")
    compile_group.add_argument("--restore-after", action="store_true",
                              help="Restaurar backups después de compilar")
    compile_group.add_argument("--no-cleanup", action="store_true",
                              help="No limpiar archivos .o después de compilar")
    
    # Argumentos comunes
    parser.add_argument("--html", help="Archivo HTML de salida (default: html/analyzer.html o html/autofix.html)")
    parser.add_argument("--json-out", help="Archivo JSON de salida (default: json/checkpatch.json o json/fixed.json)")
    
    args = parser.parse_args()
    
    # Validar argumentos según modo
    if args.analyze:
        # Configurar rutas automáticamente desde kernel root
        kernel_root = Path(args.analyze).resolve()
        if not kernel_root.exists():
            parser.error(f"Kernel root no encontrado: {kernel_root}")
        
        # Checkpatch.pl debe estar en scripts/
        checkpatch = kernel_root / "scripts" / "checkpatch.pl"
        if not checkpatch.exists():
            parser.error(f"checkpatch.pl no encontrado en {checkpatch}")
        
        # Determinar directorios a analizar
        if args.paths:
            source_dirs = [kernel_root / p for p in args.paths]
            for sd in source_dirs:
                if not sd.exists():
                    parser.error(f"Subdirectorio no encontrado: {sd}")
        else:
            source_dirs = [kernel_root]
        
        # Defaults para analyze
        args.source_dirs = source_dirs
        args.kernel_root = kernel_root
        args.checkpatch = checkpatch
        args.html = args.html or "html/analyzer.html"
        args.json_out = args.json_out or "json/checkpatch.json"
        return analyze_mode(args)
    
    elif args.fix:
        if not args.json_input:
            parser.error("--fix requiere --json-input")
        # Ajustar defaults para fix
        args.html = args.html or "html/autofix.html"
        args.json_out = args.json_out or "json/fixed.json"
        return fix_mode(args)
    
    elif args.compile:
        if not args.json_input:
            parser.error("--compile requiere --json-input")
        if not args.kernel_root:
            parser.error("--compile requiere --kernel-root")
        # Ajustar defaults para compile
        args.html = args.html or "html/compile.html"
        args.json_out = args.json_out or "json/compile.json"
        return compile_mode(args)


if __name__ == "__main__":
    sys.exit(main())
