#!/usr/bin/env python3
"""
Script para probar fixes individuales sistemáticamente
"""
import json
import subprocess
import sys
from pathlib import Path

def restore_backups():
    """Restaurar ficheros desde backups"""
    init_dir = Path("/home/kilynho/src/kernel/linux/init")
    for bak in init_dir.glob("*.bak"):
        original = bak.with_suffix("")
        subprocess.run(["cp", str(bak), str(original)], check=True)
    print("✓ Ficheros restaurados")

def run_analyzer():
    """Ejecutar análisis y devolver warnings"""
    subprocess.run([
        "python3", "main.py",
        "--analyze", "/home/kilynho/src/kernel/linux",
        "--paths", "/home/kilynho/src/kernel/linux/init"
    ], check=True, capture_output=True)
    
    with open("json/checkpatch.json") as f:
        data = json.load(f)
    
    warnings = []
    for file_data in data:
        filename = file_data['file'].split('/')[-1]
        if 'warning' in file_data:
            for w in file_data['warning']:
                warnings.append({
                    'file': filename,
                    'line': w['line'],
                    'msg': w['message']
                })
    return warnings

def test_fix(fix_name, description):
    """Probar un fix específico"""
    print(f"\n{'='*70}")
    print(f"PROBANDO: {fix_name}")
    print(f"Descripción: {description}")
    print(f"{'='*70}\n")
    
    # 1. Restaurar
    restore_backups()
    
    # 2. Análisis inicial
    print("1. Análisis ANTES del fix...")
    warnings_before = run_analyzer()
    print(f"   Warnings antes: {len(warnings_before)}")
    
    # 3. Aplicar fix (simulado - ejecutar ./run)
    print("2. Aplicando fix...")
    subprocess.run(["./run"], check=True, capture_output=True)
    
    # 4. Análisis post-fix
    print("3. Análisis DESPUÉS del fix...")
    warnings_after = run_analyzer()
    print(f"   Warnings después: {len(warnings_after)}")
    
    # 5. Comparar
    before_set = {(w['file'], w['line'], w['msg'][:50]) for w in warnings_before}
    after_set = {(w['file'], w['line'], w['msg'][:50]) for w in warnings_after}
    
    nuevos = after_set - before_set
    eliminados = before_set - after_set
    
    print(f"\n4. RESULTADO:")
    print(f"   Warnings eliminados: {len(eliminados)}")
    print(f"   Warnings NUEVOS (⚠️ bugs): {len(nuevos)}")
    
    if nuevos:
        print(f"\n   ⚠️ WARNINGS NUEVOS INTRODUCIDOS:")
        for file, line, msg in sorted(nuevos):
            print(f"      {file}:{line} - {msg}")
    
    # 6. Restaurar para siguiente test
    restore_backups()
    
    return len(eliminados), len(nuevos)

if __name__ == "__main__":
    print("TEST SISTEMÁTICO DE FIXES")
    print("="*70)
    
    # Cambiar al directorio correcto
    import os
    os.chdir("/home/kilynho/src/checkpatch")
    
    # Probar fix por fix (comentar/descomentar según necesites)
    
    # Test 1: fix_spaces_at_start_of_line
    # test_fix("fix_spaces_at_start_of_line", "Elimina espacios al inicio de líneas vacías")
    
    # Test 2: fix_printk_info multilínea
    # test_fix("fix_printk_info", "Convierte printk(KERN_INFO) a pr_info() incluyendo multilínea")
    
    print("\n✓ Para ejecutar tests, descomenta las líneas correspondientes en el script")
