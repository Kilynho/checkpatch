# Guía de Troubleshooting de Compilación

Esta guía te ayuda a entender y resolver errores de compilación cuando usas el sistema de autofix.

## 🎯 Sistema de Clasificación de Errores

El módulo de compilación clasifica automáticamente los errores en categorías:

| Tipo | Descripción | Causa | Solución |
|------|-------------|-------|----------|
| **config** | Símbolos no declarados | Falta `CONFIG_*` en `.config` | Habilitar flag en configuración |
| **dependency** | Headers faltantes | Archivo no encontrado | Verificar includes y paths |
| **code** | Errores de sintaxis/tipos | Bug real en código | Revisar/corregir código |
| **unknown** | No clasificado | Diversas causas | Análisis manual |

## 🔍 Errores Comunes y Soluciones

### 1. Errores de tipo "config"

**Síntoma:**
```
error: 'envp_init' undeclared (first use in this function)
error: redefinition of 'rd_load_image'
```

**Causa:**
Estos archivos dependen de configuraciones específicas del kernel (`CONFIG_BLK_DEV_INITRD`, `CONFIG_BLK_DEV_RAM`, etc.) que no están habilitadas en la configuración por defecto.

**Solución:**

#### Opción 1: Configuración manual específica
```bash
cd /path/to/kernel/linux
make menuconfig
# Habilitar:
# - Device Drivers → Block devices → RAM block device support
# - Device Drivers → Block devices → Initial RAM filesystem and RAM disk
make
```

#### Opción 2: Usar una configuración más completa
```bash
cd /path/to/kernel/linux
# En lugar de defconfig, usar la configuración del sistema actual
zcat /proc/config.gz > .config  # Si está disponible
# O copiar desde /boot
cp /boot/config-$(uname -r) .config
make oldconfig
```

#### Opción 3: Ignorar archivos específicos
Si no necesitas compilar estos archivos específicos, puedes filtrarlos:
```bash
# Editar tu script para excluir archivos problemáticos
exclude_files = ['do_mounts_initrd.c', 'do_mounts_rd.c']
```

### 2. Errores de tipo "dependency"

**Síntoma:**
```
fatal error: some_header.h: No such file or directory
```

**Solución:**
```bash
# Verificar que el kernel esté completamente configurado
cd /path/to/kernel/linux
make prepare
make scripts
```

### 3. Errores de tipo "code"

**Síntoma:**
```
error: expected ';' before 'return'
error: incompatible types when assigning
```

**Causa:**
Estos son errores reales en el código. Pueden ser:
- Bug del autofix
- Error preexistente en el kernel
- Cambio que requiere ajustes adicionales

**Solución:**
1. Revisar el diff del archivo modificado:
```bash
cd /path/to/kernel/linux/init
diff -u file.c.bak file.c
```

2. Si es un bug del autofix, reportarlo o deshabilitar la regla problemática en `engine.py`:
```python
# En engine.py, comentar la regla problemática:
AUTO_FIX_RULES = {
    # "regla problemática": fix_function,  # Deshabilitado por bug XYZ
}
```

### 4. Conflictos de sección `__initconst`

**Síntoma:**
```
error: 'initcall_level_names' causes a section type conflict with '__setup_str_set_debug_rodata'
```

**Causa:**
El compilador detecta que dos variables con diferentes cualificadores están en la misma sección. Esto suele ser un problema del kernel original, no del autofix.

**Solución:**
Este error suele estar presente en el kernel original. Verificar:
```bash
# Compilar archivo sin modificaciones del autofix
cd /path/to/kernel/linux
git status init/main.c  # Verificar si hay cambios
git checkout init/main.c  # Restaurar original
make init/main.o  # Si falla, es un bug del kernel original
```

## 🛠️ Auto-configuración del Kernel

El sistema automáticamente ejecuta `make defconfig` si detecta que falta `.config`. Esto:

✅ **Ventajas:**
- Configuración rápida y automática
- Permite compilar sin intervención manual
- Configuración válida y consistente

❌ **Limitaciones:**
- `defconfig` solo habilita opciones básicas
- Algunos archivos pueden requerir `CONFIG_*` específicos
- No es equivalente a una configuración completa del sistema

## 📊 Interpretar el Reporte de Compilación

### Resumen en Consola
```
============================================================
RESUMEN DE COMPILACIÓN
============================================================
Total de archivos:     10
Compilados con éxito:  7 (70.0%)
Fallidos:              3 (30.0%)
Tiempo total:          23.04s
Tiempo promedio:       2.30s
============================================================

Clasificación de errores:
  • Config/Context (símbolos no declarados por CONFIG_*): 2
  • Desconocido: 1

Archivos con errores de compilación:
  ✗ do_mounts_initrd.c [config]
    init/do_mounts_initrd.c:101:60: error: 'envp_init' undeclared...
```

### Interpretación:
- **70% de éxito** → El autofix no rompe la mayoría del código
- **2 errores [config]** → Problemas de configuración, no bugs
- **1 error [unknown]** → Requiere investigación manual

## 🔬 Verificación Avanzada

### Compilar archivo original sin modificaciones
```bash
cd /path/to/kernel/linux/init
# Restaurar original
cp file.c.bak file.c
# Compilar
cd /path/to/kernel/linux
make init/file.o
```

Si el original falla → **no es un bug del autofix**
Si el original compila pero el modificado falla → **revisar el autofix**

### Inspeccionar diferencias
```bash
# Ver exactamente qué cambió
diff -u init/file.c.bak init/file.c

# Ver con contexto coloreado
git diff --no-index init/file.c.bak init/file.c
```

### Probar fix individual
```python
# En Python
from engine import apply_fixes

issues = [{"line": 100, "message": "WARNING: quoted string split across lines"}]
results = apply_fixes("/path/to/file.c", issues)

for r in results:
    print(f"Line {r['line']}: {'✓' if r['fixed'] else '✗'} {r['message']}")
```

## 📈 Mejores Prácticas

1. **Siempre revisar el reporte de clasificación** antes de asumir que hay un bug
2. **Verificar archivos originales** antes de reportar problemas
3. **Usar configuración completa del kernel** para mejor precisión
4. **Filtrar archivos conflictivos** si no son críticos para tu análisis
5. **Mantener backups** (el sistema los crea automáticamente como `.bak`)

## 🐛 Reportar Bugs

Si encuentras un error real del autofix, incluye:

1. **Clasificación del error** (output del sistema)
2. **Diff del archivo** (`diff -u original.c modified.c`)
3. **Regla que causó el error** (buscar en `engine.py`)
4. **Contexto del código** (5-10 líneas antes/después)
5. **Versión del kernel** (si es relevante)

## 🔄 Workflow Recomendado

```bash
# 1. Analizar
./run  # o ./main.py --analyze ...

# 2. Revisar reporte de compilación
cat html/compile.html  # o consola

# 3. Si hay errores [config]:
#    a) Ignorar (son falsos positivos)
#    b) Configurar kernel manualmente
#    c) Filtrar archivos afectados

# 4. Si hay errores [code]:
#    → Investigar si es bug del autofix
#    → Revisar diff
#    → Deshabilitar regla si es necesario

# 5. Iterar
#    → Deshabilitar fixes problemáticos
#    → Re-ejecutar
#    → Verificar mejora en tasa de éxito
```

## 📚 Referencias

- [Kernel Build System](https://www.kernel.org/doc/html/latest/kbuild/index.html)
- [Kernel Configuration](https://www.kernel.org/doc/html/latest/admin-guide/README.html)
- [ARCHITECTURE.md](ARCHITECTURE.md) - Arquitectura del sistema
- [FIXES_STATUS.md](FIXES_STATUS.md) - Estado de reglas de autofix
