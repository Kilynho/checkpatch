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
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Sistema de logging
import logger

# Sistema de internacionalización
import i18n
from i18n import get_text as _

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
    logger.debug(f"[ANALYZER] args.source_dirs={args.source_dirs}, args.extensions={args.extensions}")
    all_files = []
    for source_dir in args.source_dirs:
        logger.debug(f"[ANALYZER] Buscando archivos en: {source_dir}")
        files = find_source_files(source_dir, extensions=args.extensions)
        logger.debug(f"[ANALYZER] Encontrados {len(files)} archivos en {source_dir}")
        all_files.extend(files)
    if not all_files:
        logger.error(f"[ERROR] {_('errors.files_not_found', extensions=args.extensions)}")
        return 1
    checkpatch_script = args.checkpatch
    kernel_root = args.kernel_root
    reset_analysis()
    json_data = []
    total = len(all_files)
    completed = 0
    lock = threading.Lock()
    def progress_bar(current, total):
        percent = current / total * 100
        bar_len = 40
        filled = int(bar_len * current / total)
        bar = '#' * filled + ' ' * (bar_len - filled)
        return f"[{bar}] {percent:.1f}% ({current}/{total})"
    
    logger.info(f"[ANALYZER] {_('analyzer.analyzing', total=total, workers=args.workers)}")
    files_preview = [str(f) for f in all_files[:5]]
    if len(all_files) > 5:
        files_preview.append('...')
    logger.debug(f"[ANALYZER] {_('analyzer.files_to_analyze', files=files_preview)}")
    
    logger.debug(f"[ANALYZER] Lanzando ThreadPoolExecutor con {args.workers} workers")
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(analyze_file, f, checkpatch_script, kernel_root): f for f in all_files}
        for future in as_completed(futures):
            file_path = futures[future]
            logger.debug(f"[ANALYZER] Iniciando análisis de: {file_path}")
            try:
                errors, warnings, is_correct = future.result()
                logger.debug(f"[ANALYZER] Finalizado análisis de: {file_path} - {len(errors)} errores, {len(warnings)} warnings")
                if errors or warnings:
                    json_data.append({
                        "file": str(file_path),
                        "error": errors,
                        "warning": warnings
                    })
                with lock:
                    completed += 1
                    if completed % 10 == 0 or completed == total:
                        print(f"\r[ANALYZER] Progreso: {progress_bar(completed, total)}", end="")
                    logger.debug(f"[ANALYZER] {_('analyzer.analyzed_file', file=file_path, errors=len(errors), warnings=len(warnings))}")
                
            except Exception as e:
                logger.error(f"\n[ERROR] {_('errors.file_error', file=file_path, error=e)}")
    
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
    
    logger.info(f"[ANALYZER] {_('analyzer.errors_found', count=error_count)}")
    logger.info(f"[ANALYZER] {_('analyzer.warnings_found', count=warning_count)}")
    logger.info(f"[ANALYZER] {_('analyzer.total_found', count=error_count + warning_count)}")
    logger.info(f"[ANALYZER] {_('analyzer.analysis_complete')}")
    logger.info(f"[ANALYZER] {_('analyzer.html_generated', path=html_path)}")
    logger.info(f"[ANALYZER] {_('analyzer.json_generated', path=json_path)}")
    
    return 0


def fix_mode(args):
    """Modo autofix: aplica correcciones automáticas."""
    
    json_file = Path(args.json_input)
    if not json_file.exists():
        logger.error(f"[ERROR] {_('errors.file_not_exist', file=json_file)}")
        return 1
    
    with open(json_file, "r") as f:
        files_data = json.load(f)
    
    # Estructura para report_data
    from collections import defaultdict
    report_data = defaultdict(lambda: {"warning": [], "error": []})
    modified_files = set()
    
    file_filter = Path(args.file).resolve() if args.file else None
    
    logger.info(f"[AUTOFIX] {_('autofix.processing')}")
    logger.debug(f"[AUTOFIX] {_('autofix.json_input', json_file=json_file, filter=file_filter)}")
    
    for entry in files_data:
        file_path = Path(entry["file"]).resolve()
        logger.debug(f"[AUTOFIX] Procesando archivo: {file_path}")
        if file_filter and file_filter != file_path:
            logger.debug(f"[AUTOFIX] Archivo filtrado: {file_path} (filtro: {file_filter})")
            continue
        # Reunir issues según tipo
        issues_to_fix = []
        if args.type in ("warning", "all"):
            for w in entry.get("warning", []):
                issues_to_fix.append({"type": "warning", **w})
        if args.type in ("error", "all"):
            for e in entry.get("error", []):
                issues_to_fix.append({"type": "error", **e})
        logger.debug(f"[AUTOFIX] Issues a corregir: {len(issues_to_fix)}")
        if not issues_to_fix:
            logger.debug(f"[AUTOFIX] Ningún issue para corregir en: {file_path}")
            continue
        issues_to_fix.sort(key=lambda x: -x["line"])  # de abajo hacia arriba
        logger.debug(f"[AUTOFIX] Issues ordenados para aplicar fixes")
        # Aplicar fixes
        logger.debug(f"[AUTOFIX] Llamando a apply_fixes para {file_path}")
        fix_results = apply_fixes(file_path, issues_to_fix)
        logger.debug(f"[AUTOFIX] apply_fixes completado para {file_path}")
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
            logger.info(f"[AUTOFIX]  - {file_path.relative_to(file_path.parent.parent.parent)}")
            logger.debug(f"[AUTOFIX] {_('autofix.modified_file', file=file_path)}")
    
    # Calcular estadísticas para resumen
    errors_fixed = sum(1 for issues in report_data.values() for i in issues.get("error", []) if i.get("fixed"))
    warnings_fixed = sum(1 for issues in report_data.values() for i in issues.get("warning", []) if i.get("fixed"))
    errors_skipped = sum(1 for issues in report_data.values() for i in issues.get("error", []) if not i.get("fixed"))
    warnings_skipped = sum(1 for issues in report_data.values() for i in issues.get("warning", []) if not i.get("fixed"))
    
    # Resumen en consola
    if errors_fixed + errors_skipped > 0:
        logger.info(f"[AUTOFIX] {_('autofix.errors_processed', total=errors_fixed + errors_skipped)}")
        logger.info(f"[AUTOFIX]  - {_('autofix.fixed', count=errors_fixed, percent=100*errors_fixed/(errors_fixed+errors_skipped))}")
        logger.info(f"[AUTOFIX]  - {_('autofix.skipped', count=errors_skipped, percent=100*errors_skipped/(errors_fixed+errors_skipped))}")
    
    if warnings_fixed + warnings_skipped > 0:
        logger.info(f"[AUTOFIX] {_('autofix.warnings_processed', total=warnings_fixed + warnings_skipped)}")
        logger.info(f"[AUTOFIX]  - {_('autofix.fixed', count=warnings_fixed, percent=100*warnings_fixed/(warnings_fixed+warnings_skipped))}")
        logger.info(f"[AUTOFIX]  - {_('autofix.skipped', count=warnings_skipped, percent=100*warnings_skipped/(warnings_fixed+warnings_skipped))}")
    
    total = errors_fixed + warnings_fixed + errors_skipped + warnings_skipped
    total_fixed = errors_fixed + warnings_fixed
    if total > 0:
        logger.info(f"[AUTOFIX] {_('autofix.total_processed', total=total)}")
        logger.info(f"[AUTOFIX]  - {_('autofix.fixed', count=total_fixed, percent=100*total_fixed/total)}")
        logger.info(f"[AUTOFIX]  - {_('autofix.skipped', count=total - total_fixed, percent=100*(total-total_fixed)/total)}")
    
    # Generar HTML
    html_path = Path(args.html)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    logger.debug(f"[AUTOFIX] Generando HTML principal: {html_path}")
    generate_autofix_html(report_data, html_path)
    logger.debug(f"[AUTOFIX] Generando HTML detalle motivo: {html_path.parent / 'autofix-detail-reason.html'}")
    generate_autofix_detail_reason_html(report_data, html_path.parent / "autofix-detail-reason.html")
    logger.debug(f"[AUTOFIX] Generando HTML detalle archivo: {html_path.parent / 'autofix-detail-file.html'}")
    generate_autofix_detail_file_html(report_data, html_path.parent / "autofix-detail-file.html")
    # Generar dashboard
    dashboard_path = html_path.parent / "dashboard.html"
    logger.debug(f"[AUTOFIX] Generando dashboard: {dashboard_path}")
    generate_dashboard_html(dashboard_path)
    # Guardar JSON de resultados
    json_out_path = Path(args.json_out)
    json_out_path.parent.mkdir(parents=True, exist_ok=True)
    logger.debug(f"[AUTOFIX] Guardando JSON de resultados: {json_out_path}")
    with open(json_out_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, default=str)
    
    logger.info(f"[AUTOFIX] {_('autofix.complete', path=json_out_path)}")
    logger.info(f"[AUTOFIX] {_('autofix.html_generated', path=html_path)}")
    logger.info(f"[AUTOFIX] {_('autofix.json_generated', path=json_out_path)}")
    
    return 0


def compile_mode(args):
    """Modo compilación: compila archivos modificados y verifica que compilen."""
    
    json_file = Path(args.json_input)
    if not json_file.exists():
        logger.error(f"[ERROR] {_('errors.file_not_exist', file=json_file)}")
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
        logger.info(f"[COMPILE] {_('compile.no_modified_files')}")
        return 0
    
    logger.debug(f"[COMPILE] {_('compile.files_to_compile', files=[str(f) for f in modified_files])}")
    
    # Restaurar backups si se solicita
    if args.restore_before:
        logger.info(f"[COMPILE] {_('compile.restoring', count=len(modified_files))}")
        restore_backups(modified_files)
    
    # Compilar archivos
    kernel_root = Path(args.kernel_root).resolve()
    if not kernel_root.exists():
        logger.error(f"[ERROR] {_('errors.kernel_not_found', path=kernel_root)}")
        return 1
    
    logger.info(f"[COMPILE] {_('compile.kernel_root', path=kernel_root)}")
    results = compile_modified_files(
        modified_files, 
        kernel_root, 
        cleanup=not args.no_cleanup
    )
    
    # Restaurar backups después si se solicita
    if args.restore_after:
        logger.info(f"\n[COMPILE] {_('compile.restoring', count=len(modified_files))}")
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
    
    logger.info(f"\n[COMPILE] {_('compile.html_generated', path=html_path)}")
    logger.info(f"[COMPILE] {_('compile.json_generated', path=json_path)}")
    
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
    
    # Argumentos de logging
    logging_group = parser.add_argument_group("Opciones de logging")
    logging_group.add_argument("--log-level", 
                              choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                              default="INFO",
                              help="Nivel de logging (default: INFO)")
    logging_group.add_argument("--log-file", 
                              help="Archivo de log opcional (ej: logs/checkpatch.log)")
    logging_group.add_argument("--no-color", action="store_true",
                              help="Desactivar colores en la salida de consola")
    logging_group.add_argument("--language", choices=["es", "en"], default="es",
                              help="Idioma de la interfaz (default: es)")
    
    args = parser.parse_args()
    
    # Configurar idioma
    i18n.set_language(args.language)
    
    # Configurar logging
    log_level = logger.get_level_from_string(args.log_level)
    logger.setup_logging(
        level=log_level,
        log_file=args.log_file,
        use_colors=not args.no_color
    )
    
    logger.debug(f"[MAIN] {_('main.arguments', args=vars(args))}")
    logger.debug(f"[MAIN] {_('main.log_level', level=args.log_level)}")
    
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
        # Ajustar defaults para fix
        args.json_input = args.json_input or "json/checkpatch.json"
        args.html = args.html or "html/autofix.html"
        args.json_out = args.json_out or "json/fixed.json"
        return fix_mode(args)
    
    elif args.compile:
        # Ajustar defaults para compile
        args.json_input = args.json_input or "json/fixed.json"
        args.kernel_root = kernel_root
        args.html = args.html or "html/compile.html"
        args.json_out = args.json_out or "json/compile.json"
        return compile_mode(args)


if __name__ == "__main__":
    sys.exit(main())
