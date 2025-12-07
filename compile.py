#!/usr/bin/env python3
"""
compile.py - Módulo para compilación de archivos modificados del kernel Linux

Este módulo permite:
- Compilar archivos individuales del kernel Linux
- Verificar que los fixes aplicados no rompen la compilación
- Limpiar archivos compilados sin dejar rastro
- Generar reportes de compilación en HTML, JSON y consola
"""

import subprocess
import os
import shutil
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import json
import time


class CompilationResult:
    """Representa el resultado de compilar un archivo."""
    
    def __init__(self, file_path: str, success: bool, duration: float, 
                 stdout: str = "", stderr: str = "", error_message: str = ""):
        self.file_path = file_path
        self.success = success
        self.duration = duration
        self.stdout = stdout
        self.stderr = stderr
        self.error_message = error_message
    
    def to_dict(self) -> dict:
        """Convierte el resultado a un diccionario para JSON."""
        return {
            "file": self.file_path,
            "success": self.success,
            "duration": self.duration,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "error_message": self.error_message
        }


def compile_single_file(file_path: Path, kernel_root: Path) -> CompilationResult:
    """
    Compila un archivo individual del kernel Linux usando el sistema de build del kernel.
    
    Args:
        file_path: Ruta al archivo .c a compilar
        kernel_root: Directorio raíz del kernel Linux
    
    Returns:
        CompilationResult con el resultado de la compilación
    """
    try:
        # Convertir la ruta del archivo .c a la ruta del .o correspondiente
        rel_path = file_path.relative_to(kernel_root)
        obj_path = rel_path.with_suffix('.o')
        
        start_time = time.time()
        
        # Usar make con el target específico del archivo .o
        # Esto compila solo ese archivo sin compilar todo el kernel
        result = subprocess.run(
            ['make', str(obj_path)],
            cwd=str(kernel_root),
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos timeout
        )
        
        duration = time.time() - start_time
        
        success = result.returncode == 0
        error_msg = ""
        
        if not success:
            # Extraer mensaje de error más relevante
            error_lines = result.stderr.split('\n')
            # Buscar líneas con "error:" 
            error_msgs = [line for line in error_lines if 'error:' in line.lower()]
            if error_msgs:
                error_msg = '\n'.join(error_msgs[:5])  # Primeros 5 errores
            else:
                error_msg = result.stderr[:500]  # Primeros 500 chars si no hay errores explícitos
        
        return CompilationResult(
            file_path=str(file_path),
            success=success,
            duration=duration,
            stdout=result.stdout,
            stderr=result.stderr,
            error_message=error_msg
        )
        
    except subprocess.TimeoutExpired:
        return CompilationResult(
            file_path=str(file_path),
            success=False,
            duration=300.0,
            error_message="Timeout: Compilation took more than 5 minutes"
        )
    except Exception as e:
        return CompilationResult(
            file_path=str(file_path),
            success=False,
            duration=0.0,
            error_message=f"Exception during compilation: {str(e)}"
        )


def cleanup_compiled_files(kernel_root: Path, compiled_files: List[Path]):
    """
    Limpia los archivos .o generados por la compilación.
    
    Args:
        kernel_root: Directorio raíz del kernel
        compiled_files: Lista de archivos .c que fueron compilados
    """
    for c_file in compiled_files:
        try:
            # Encontrar el archivo .o correspondiente
            rel_path = c_file.relative_to(kernel_root)
            obj_path = kernel_root / rel_path.with_suffix('.o')
            
            if obj_path.exists():
                obj_path.unlink()
                print(f"[CLEANUP] Removed: {obj_path.relative_to(kernel_root)}")
            
            # También limpiar posibles archivos auxiliares (.cmd, .d, etc.)
            cmd_file = obj_path.parent / f".{obj_path.name}.cmd"
            if cmd_file.exists():
                cmd_file.unlink()
            
            d_file = obj_path.with_suffix('.o.d')
            if d_file.exists():
                d_file.unlink()
                
        except Exception as e:
            print(f"[CLEANUP WARNING] Could not clean {c_file}: {e}")


def compile_modified_files(files: List[Path], kernel_root: Path, 
                          cleanup: bool = True) -> List[CompilationResult]:
    """
    Compila una lista de archivos modificados del kernel.
    
    Args:
        files: Lista de archivos .c a compilar
        kernel_root: Directorio raíz del kernel Linux
        cleanup: Si True, limpia los archivos .o después de compilar
    
    Returns:
        Lista de CompilationResult con los resultados
    """
    results = []
    
    print(f"[COMPILE] Compilando {len(files)} archivos...")
    
    for i, file_path in enumerate(files, 1):
        # Solo compilar archivos .c
        if file_path.suffix != '.c':
            print(f"[COMPILE] [{i}/{len(files)}] Skipped (not .c): {file_path.name}")
            continue
        
        print(f"[COMPILE] [{i}/{len(files)}] Compiling: {file_path.relative_to(kernel_root)}")
        
        result = compile_single_file(file_path, kernel_root)
        results.append(result)
        
        if result.success:
            print(f"[COMPILE]   ✓ Success ({result.duration:.2f}s)")
        else:
            print(f"[COMPILE]   ✗ Failed ({result.duration:.2f}s)")
            if result.error_message:
                # Mostrar solo primera línea del error
                first_error = result.error_message.split('\n')[0]
                print(f"[COMPILE]     Error: {first_error}")
    
    if cleanup:
        compiled_c_files = [Path(r.file_path) for r in results if r.success]
        if compiled_c_files:
            print(f"\n[CLEANUP] Limpiando {len(compiled_c_files)} archivos compilados...")
            cleanup_compiled_files(kernel_root, compiled_c_files)
    
    return results


def restore_backups(files: List[Path]):
    """
    Restaura los archivos desde sus backups (.bak).
    
    Args:
        files: Lista de archivos a restaurar
    """
    restored = 0
    for file_path in files:
        backup_path = file_path.with_suffix(file_path.suffix + ".bak")
        if backup_path.exists():
            shutil.copy2(backup_path, file_path)
            restored += 1
            print(f"[RESTORE] Restored: {file_path.name}")
    
    if restored > 0:
        print(f"[RESTORE] ✓ Restored {restored} files from backup")
    else:
        print("[RESTORE] No backup files found to restore")


def summarize_results(results: List[CompilationResult]) -> Dict:
    """
    Genera un resumen de los resultados de compilación.
    
    Args:
        results: Lista de CompilationResult
    
    Returns:
        Diccionario con estadísticas
    """
    total = len(results)
    successful = sum(1 for r in results if r.success)
    failed = total - successful
    total_duration = sum(r.duration for r in results)
    avg_duration = total_duration / total if total > 0 else 0
    
    return {
        "total": total,
        "successful": successful,
        "failed": failed,
        "success_rate": (successful / total * 100) if total > 0 else 0,
        "total_duration": total_duration,
        "avg_duration": avg_duration
    }


def print_summary(results: List[CompilationResult]):
    """
    Imprime un resumen de los resultados en consola.
    
    Args:
        results: Lista de CompilationResult
    """
    summary = summarize_results(results)
    
    print("\n" + "="*60)
    print("RESUMEN DE COMPILACIÓN")
    print("="*60)
    print(f"Total de archivos:     {summary['total']}")
    print(f"Compilados con éxito:  {summary['successful']} ({summary['success_rate']:.1f}%)")
    print(f"Fallidos:              {summary['failed']} ({100 - summary['success_rate']:.1f}%)")
    print(f"Tiempo total:          {summary['total_duration']:.2f}s")
    print(f"Tiempo promedio:       {summary['avg_duration']:.2f}s")
    print("="*60)
    
    if summary['failed'] > 0:
        print("\nArchivos con errores de compilación:")
        for result in results:
            if not result.success:
                print(f"  ✗ {Path(result.file_path).name}")
                if result.error_message:
                    # Mostrar primera línea de error
                    first_line = result.error_message.split('\n')[0]
                    print(f"    {first_line[:80]}")


def save_json_report(results: List[CompilationResult], output_path: Path):
    """
    Guarda los resultados de compilación en formato JSON.
    
    Args:
        results: Lista de CompilationResult
        output_path: Ruta donde guardar el archivo JSON
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    summary = summarize_results(results)
    
    data = {
        "summary": summary,
        "results": [r.to_dict() for r in results]
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"[COMPILE] ✓ JSON generado: {output_path}")
