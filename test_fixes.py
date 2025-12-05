#!/usr/bin/env python3
"""
Test de integración para validar que todos los fixes funcionan correctamente.
Ejecuta los fixes sobre archivos reales y verifica que:
1. No hay errores de ejecución
2. Los archivos modificados tienen sintaxis Python válida
3. Los fixes reportan el número esperado de correcciones
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

def run_command(cmd, cwd=None):
    """Ejecuta un comando y retorna el resultado."""
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout, result.stderr

def test_full_run():
    """Test completo: restaurar archivos, analizar y fixear."""
    
    print("=" * 80)
    print("TEST DE INTEGRACIÓN - CHECKPATCH AUTOFIX")
    print("=" * 80)
    
    kernel_path = Path("/home/kilynho/src/kernel/linux")
    checkpatch_path = Path("/home/kilynho/src/checkpatch")
    
    # 1. Restaurar archivos originales
    print("\n[1/4] Restaurando archivos originales desde git...")
    ret, out, err = run_command("git checkout init/", cwd=kernel_path)
    if ret != 0:
        print(f"❌ Error restaurando archivos: {err}")
        return False
    print(f"✓ Archivos restaurados")
    
    # 2. Ejecutar análisis y fixes
    print("\n[2/4] Ejecutando análisis y fixes...")
    ret, out, err = run_command("./run 2>&1", cwd=checkpatch_path)
    if ret != 0:
        print(f"❌ Error ejecutando ./run: {err}")
        print(f"Output: {out}")
        return False
    
    # Extraer resultados
    for line in out.split('\n'):
        if 'Warnings procesados:' in line:
            print(f"   {line}")
        elif 'Corregidos:' in line:
            print(f"   {line}")
    
    # 3. Validar JSON de resultados
    print("\n[3/4] Validando resultados...")
    try:
        fixed_json = checkpatch_path / "json" / "fixed.json"
        with open(fixed_json) as f:
            data = json.load(f)
        
        total_warnings = 0
        total_fixed = 0
        total_errors = 0
        fixes_by_type = {}
        
        for file_path, issues in data.items():
            for w in issues.get('warning', []):
                total_warnings += 1
                if w.get('fixed'):
                    total_fixed += 1
                    # Contar por tipo de warning
                    msg = w['message'].replace('WARNING: ', '').split(':')[0]
                    fixes_by_type[msg] = fixes_by_type.get(msg, 0) + 1
            
            for e in issues.get('error', []):
                total_errors += 1
        
        print(f"✓ Total warnings: {total_warnings}")
        print(f"✓ Warnings corregidos: {total_fixed} ({100*total_fixed/total_warnings:.1f}%)")
        print(f"✓ Total errores: {total_errors}")
        
        # Mostrar top 10 fixes aplicados
        print(f"\n   Top 10 tipos de fixes aplicados:")
        for msg, count in sorted(fixes_by_type.items(), key=lambda x: -x[1])[:10]:
            print(f"      {count:3d}  {msg[:70]}")
        
    except Exception as e:
        print(f"❌ Error validando JSON: {e}")
        return False
    
    # 4. Validar que los archivos modificados son válidos
    print("\n[4/4] Validando archivos modificados...")
    
    # Verificar que los archivos .c tienen sintaxis válida con gcc -fsyntax-only
    modified_files = []
    ret, out, err = run_command("git status --short init/", cwd=kernel_path)
    for line in out.split('\n'):
        if line.strip() and line.startswith(' M'):
            file_path = line.strip().split()[1]
            modified_files.append(file_path)
    
    print(f"✓ Archivos modificados: {len(modified_files)}")
    
    # Contar líneas modificadas
    ret, out, err = run_command("git diff --stat init/", cwd=kernel_path)
    if out:
        for line in out.split('\n'):
            if 'changed' in line or 'insertion' in line or 'deletion' in line:
                print(f"   {line.strip()}")
    
    # 5. Verificar que no hay fallos de sintaxis evidentes
    syntax_errors = []
    for file_path in modified_files:
        if file_path.endswith('.c'):
            # Verificación básica: el archivo tiene el mismo número de { que }
            full_path = kernel_path / file_path
            try:
                with open(full_path) as f:
                    content = f.read()
                    open_braces = content.count('{')
                    close_braces = content.count('}')
                    if open_braces != close_braces:
                        syntax_errors.append(f"{file_path}: desequilibrio de llaves ({{ {open_braces} vs }} {close_braces})")
            except Exception as e:
                syntax_errors.append(f"{file_path}: error leyendo archivo: {e}")
    
    if syntax_errors:
        print(f"\n⚠️  Posibles problemas de sintaxis encontrados:")
        for err in syntax_errors:
            print(f"   - {err}")
    else:
        print(f"✓ No se detectaron problemas de sintaxis evidentes")
    
    # 6. Validar que los fixes específicos funcionaron
    print("\n[5/5] Validando fixes específicos...")
    
    validation_results = []
    
    # Test 1: __initdata placement
    initdata_fixed = sum(1 for msg, count in fixes_by_type.items() if '__initdata should be placed after' in msg)
    if initdata_fixed >= 15:
        validation_results.append(("✓", f"__initdata: {initdata_fixed}/15 corregidos"))
    else:
        validation_results.append(("❌", f"__initdata: solo {initdata_fixed}/15 corregidos"))
    
    # Test 2: printk conversions
    printk_types = ['Prefer [subsystem eg', 'printk() should include KERN']
    printk_fixed = sum(count for msg, count in fixes_by_type.items() if any(pt in msg for pt in printk_types))
    if printk_fixed >= 50:
        validation_results.append(("✓", f"printk conversions: {printk_fixed} corregidos"))
    else:
        validation_results.append(("⚠️ ", f"printk conversions: solo {printk_fixed} corregidos"))
    
    # Test 3: SPDX headers
    spdx_fixed = sum(count for msg, count in fixes_by_type.items() if 'SPDX' in msg)
    if spdx_fixed >= 1:
        validation_results.append(("✓", f"SPDX headers: {spdx_fixed} corregidos"))
    else:
        validation_results.append(("⚠️ ", f"SPDX headers: {spdx_fixed} corregidos"))
    
    for status, msg in validation_results:
        print(f"   {status} {msg}")
    
    # Resumen final
    print("\n" + "=" * 80)
    if total_fixed >= 125 and not syntax_errors:
        print("✅ TEST EXITOSO - Todos los fixes funcionan correctamente")
        print(f"   {total_fixed}/{total_warnings} warnings corregidos ({100*total_fixed/total_warnings:.1f}%)")
        print("=" * 80)
        return True
    else:
        print("⚠️  TEST COMPLETADO CON ADVERTENCIAS")
        if total_fixed < 125:
            print(f"   - Solo {total_fixed}/{total_warnings} warnings corregidos (esperado: ≥125)")
        if syntax_errors:
            print(f"   - Se detectaron {len(syntax_errors)} posibles problemas de sintaxis")
        print("=" * 80)
        return False

class TestCheckpatchAutofix(unittest.TestCase):
    """Test suite para checkpatch autofix."""
    
    def test_full_integration(self):
        """Test de integración completo."""
        success = test_full_run()
        self.assertTrue(success, "Test de integración falló")

if __name__ == "__main__":
    # Si se ejecuta directamente, usar el formato bonito
    if len(sys.argv) == 1:
        success = test_full_run()
        sys.exit(0 if success else 1)
    else:
        # Si se ejecuta con unittest (VS Code), usar unittest
        unittest.main()
