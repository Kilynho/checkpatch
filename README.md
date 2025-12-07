# Checkpatch - Analyzer & Autofix System

**Toda la documentación se encuentra ahora en la carpeta `Documentation/`.**

Consulte los archivos dentro de `Documentation/` para guías, arquitectura, troubleshooting y referencias.

Sistema unificado para análisis y corrección automática de warnings/errores de **checkpatch.pl** (Linux kernel).

## 🚀 Inicio Rápido

### Instalación

```bash
# Clonar o descargar el repositorio
cd checkpatch

# Dar permisos de ejecución
chmod +x main.py test.py run
```

### Uso Básico

```bash
# 1. Analizar archivos con checkpatch
./main.py --analyze /path/to/kernel/linux --paths init

# 2. Ver reporte (abrir en navegador)
open html/dashboard.html

# 3. Aplicar fixes automáticos
./main.py --fix --json-input json/checkpatch.json

# 4. Compilar archivos modificados (verifica que compilen)
./main.py --compile --json-input json/fixed.json --kernel-root /path/to/kernel/linux --restore-after

# 5. Ver resultados
open html/dashboard.html  # Se actualizó automáticamente
```

O ejecutar todo automáticamente:
```bash
./run
```

---

## 📋 Estructura del Proyecto

```
checkpatch/
├── main.py              # Punto de entrada (--analyze, --fix, --compile)
├── engine.py            # Lógica análisis y fixes
├── core.py              # Implementaciones de fixes (40+)
├── compile.py           # Módulo de compilación de archivos
├── report.py            # Generadores de HTML (8 reportes)
├── utils.py             # Utilidades comunes
├── constants.py         # Constantes y patterns
├── test.py              # Tests de integración
├── test_fixes.py        # Tests unitarios de fixes
├── test_compile.py      # Tests unitarios de compilación
├── run                  # Script automatizado
│
├── README.md            # Este archivo
├── ARCHITECTURE.md      # Arquitectura detallada
├── CHANGELOG.md         # Historial de cambios
├── HTML_REPORTS.md      # Estructura de reportes
├── QUICK_REFERENCE.md   # Guía rápida
│
├── html/                # Reportes generados
│   ├── dashboard.html           # Hub principal
│   ├── analyzer.html            # Resumen análisis
│   ├── detail-reason.html       # Detalles por tipo (analyzer)
│   ├── detail-file.html         # Detalles por fichero (analyzer)
│   ├── autofix.html             # Resumen autofix
│   ├── autofix-detail-reason.html   # Detalles por tipo (autofix)
│   ├── autofix-detail-file.html     # Detalles por fichero (autofix)
│   └── compile.html             # Reporte de compilación
│
├── json/                # Datos procesados
│   ├── checkpatch.json  # Issues encontradas
│   ├── fixed.json       # Issues fijadas
│   └── compile.json     # Resultados de compilación
│
└── __pycache__/         # Cache Python (ignorar)
```

---

## 📊 Reportes HTML

Sistema modular de **8 reportes interconectados** con navegación por breadcrumbs:

### Sección Analyzer (Análisis Inicial)

| Reporte | Tamaño | Propósito |
|---------|--------|----------|
| **analyzer.html** | 41K | Resumen de issues (tabla de rankings) |
| **detail-reason.html** | 21K | Detalles por tipo de error/warning |
| **detail-file.html** | 64K | Detalles por fichero (expandibles) |

**Flujo:** analyzer → (clic motivo) → detail-reason → (clic fichero) → detail-file

### Sección Autofix (Correcciones Automáticas)

| Reporte | Tamaño | Propósito |
|---------|--------|----------|
| **autofix.html** ⭐ | 9K | Resumen + executive boxes (éxito %) |
| **autofix-detail-reason.html** ⭐ | 3.8K | Detalles por tipo + fix-type cards |
| **autofix-detail-file.html** ⭐ | 18K | Detalles por fichero + file grid |

**Flujo:** autofix → (clic tipo) → autofix-detail-reason → (clic fichero) → autofix-detail-file

### Sección Compile (Verificación de Compilación) ⭐ NUEVO

| Reporte | Propósito |
|---------|----------|
| **compile.html** ⭐ | Resultados de compilación con estadísticas de éxito/fallo |

**Características:**
- Muestra archivos compilados exitosamente y con errores
- Estadísticas visuales con tarjetas de resumen
- Detalles expandibles con errores de compilación
- Tiempo de compilación por archivo

### Hub Central

| Reporte | Tamaño | Propósito |
|---------|--------|----------|
| **dashboard.html** | 6.6K | Navegación central con breadcrumb (tabs: Analyzer, Autofix, Compile) |

---

## 🎯 Características

### ✅ Analyzer
- Análisis paralelo con `checkpatch.pl`
- Clasificación automática por tipo de error
- Reporte multi-nivel (summary → details)
- Colorización ERROR/WARNING
- Cross-linking entre páginas

### ✅ Autofix
- 40+ reglas de corrección automática
- Fixea: strings, indentación, comentarios, printk, strcpy, etc.
- Backup automático (.bak)
- Reporte visual con executive summary
- Estadísticas: tasa de éxito, ficheros procesados

### ✅ Dashboard
- Navegación por tabs (Analyzer, Autofix)
- Breadcrumb dinámico que muestra ruta
- Iframe viewer para reportes
- Deep linking con hash (#) para auto-expand
- Link hijacking (click en links internos = carga en iframe)

### ✅ HTML Responsivo
- Diseño mobile-friendly
- CSS Grid responsive
- Expandibles HTML5 (`<details>`)
- Auto-scroll a anchors
- Sin dependencias externas

---

## 📈 Estadísticas Actuales

### Análisis (linux/init - 14 archivos)
```
Issues totales:         168
  ├─ Errores:           16 (68.8% corregidos)
  └─ Warnings:          152 (78.3% corregidos)
```

### Autofix
```
Total procesados:       168
  ├─ Corregidos:        127 (75.6%)
  └─ Saltados:          41 (24.4%)
Ficheros modificados:   11/14 (78.6%)
```

### Compilación
```
Archivos compilables:   10
  ├─ Éxitos:            7 (70.0%)
  └─ Fallos:            3 (30.0%)
Tiempo promedio:        2.30s/archivo

Clasificación de errores:
  ├─ Config/Context:    2 (símbolos no declarados por CONFIG_*)
  └─ Desconocido:       1 (conflicto de sección)
```

**Nota sobre errores de compilación:**
Los 3 fallos son errores de **configuración/contexto del kernel**, no bugs del autofix:
- `do_mounts_initrd.c`: `envp_init` no declarado (requiere CONFIG_BLK_DEV_INITRD)
- `do_mounts_rd.c`: Redefinición de funciones (requiere configuración específica)
- `main.c`: Conflicto de sección `__initconst` (problema del kernel original)

El sistema de compilación ahora:
✅ Auto-configura el kernel (`make defconfig`) si falta `.config`
✅ Clasifica errores por tipo (config, code, dependency, unknown)
✅ Distingue bugs de autofix vs problemas del entorno

---

## 🔧 Commandos Principales

### Análisis
```bash
./main.py --analyze --source-dir linux/init
./main.py --analyze --source-dir linux/init --extensions .c .h
```

Genera:
- `html/analyzer.html` (+ detail-reason + detail-file)
- `html/dashboard.html`
- `json/checkpatch.json`

### Autofix
```bash
./main.py --fix --json-input json/checkpatch.json
./main.py --fix --json-input json/checkpatch.json --type warning  # solo warnings
```

Genera:
- `html/autofix.html` (+ detail-reason + detail-file)
- `json/fixed.json`
- Actualiza archivos con correcciones

### Compilación ⭐ NUEVO
```bash
# Compilar archivos modificados después de autofix
./main.py --compile --json-input json/fixed.json --kernel-root /path/to/kernel/linux

# Compilar y restaurar backups después
./main.py --compile --json-input json/fixed.json --kernel-root /path/to/kernel/linux --restore-after

# Compilar sin limpiar archivos .o
./main.py --compile --json-input json/fixed.json --kernel-root /path/to/kernel/linux --no-cleanup
```

Genera:
- `html/compile.html` - Reporte visual de compilación
- `json/compile.json` - Resultados en formato JSON
- Salida en consola con resumen de éxito/fallos

Características:
- Compila archivos uno por uno usando el sistema de build del kernel
- No deja archivos .o en el kernel (limpieza automática)
- Puede restaurar backups antes/después de compilar
- Muestra errores de compilación detallados

### Tests
```bash
# Tests de integración (requiere kernel Linux)
./test.py                          # Ejecuta test de integración completo

# Tests unitarios (no requiere dependencias externas)
./test_fixes.py                    # Tests de fixes (32 tests)
./test_compile.py                  # Tests de compilación (10 tests)
./test_compile.py -v               # Ejecuta con salida detallada

# Test específico
python3 -m unittest test_fixes.TestFixFunctions.test_fix_indent_tabs
python3 -m unittest test_compile.TestCompilationResult.test_compilation_result_success
```

Los tests unitarios se ejecutan automáticamente en CI/CD con GitHub Actions en cada push.
Ver `TESTING.md` para documentación completa sobre cómo agregar tests para nuevos fixes.

### Script Automatizado
```bash
./run  # Ejecuta: analyze → autofix → compile → muestra resumen
```

---

## 🐛 Fixes Soportados

### Indentación (9 fix types)
- Espacios → tabulaciones (`INDENT_WITH_TABS`)
- Tabulaciones incompletas (`INDENT_CONTINUATION`)

### Espaciado (8 fix types)
- Espacios después de comas (`SPACE_AFTER_COMMA`)
- Espacios en operadores (`SPACING`)
- Líneas en blanco (`MISSING_BLANK_LINE`)

### Strings (3 fix types)
- Strings multi-línea (`QUOTED_STRING_SPLIT`)
- Concatenación de strings

### Comentarios (2 fix types)
- Falta SPDX license (`MISSING_SPDX`)
- Formato de bloques de comentario

### Funciones Obsoletas (10+ fix types)
- `strcpy()` → `strscpy()` (`STRCPY_TO_STRSCPY`)
- `simple_strtoul()` → `kstrtoul()` (`SIMPLE_STRTOUL_TO_KSTRTOUL`)
- `printk()` → `pr_*()` / `dev_*()` (`PRINTK_TO_PR_*`)

### Manejo de Memoria & Seguridad (5+ fix types)
- Comparaciones jiffies (`JIFFIES_COMPARISON`)
- Permisos simbólicos → octales (`SYMBOLIC_PERMS`)

Y más... ver `FIXES_STATUS.md`

---

## 📚 Documentación

- **ARCHITECTURE.md** - Estructura de módulos y flujo general
- **HTML_REPORTS.md** - Arquitectura de 7 reportes HTML
- **CHANGELOG.md** - Historial de cambios y versiones
- **TESTING.md** ⭐ - Guía completa para escribir tests y agregar nuevos fixes
- **QUICK_REFERENCE.md** - Guía rápida URLs y contenidos
- **FIXES_STATUS.md** - Estado de cada fix soportado
- **FALSOS_POSITIVOS_ANALISIS.md** - Análisis de false positives

---

## 🧪 Testing

```bash
# Correr todos los tests
./test.py

# Salida esperada
Ran 6 tests in ~2.5s
OK

# Tests incluyen:
- Análisis básico
- Aplicación de fixes
- Generación HTML
- Integración completa
```

---

## 🎨 Estilos & Colores

**Colores utilizados:**
- 🔴 ERROR: Rojo #d32f2f (+ fondo claro)
- 🟠 WARNING: Naranja #f57c00 (+ fondo claro)
- 🟢 FIXED: Verde #2e7d32
- ⚪ SKIPPED: Gris #757575

**Elementos responsivos:**
- Tablas: Ancho 100%, scroll horizontal en mobile
- Grids: `repeat(auto-fit, minmax(250px, 1fr))`
- Expandibles: Clic para abrir/cerrar
- Badgets: Contadores visuales

---

## 🔄 Flujo de Datos

```
checkpatch.pl (kernel tool)
        ↓
analyze_file() → engine.py
        ↓
analysis_data (dict)
        ↓
generate_*_html() → report.py → 7 HTML files
        ↓
dashboard.html (iframe viewer)
        ↓
[Usuario abre en navegador]
```

**Para autofix:**
```
json/checkpatch.json
        ↓
apply_fixes() → engine.py
        ↓
[archivos modificados en lugar]
        ↓
generate_autofix_*_html() → 3 HTML files
        ↓
json/fixed.json (resultados)
```

---

## 🚀 CI/CD y Testing

### ✅ Tests Automáticos
- **32 tests unitarios** para todos los fixes implementados
- Tests se ejecutan automáticamente en **GitHub Actions** en cada push/PR
- No requieren dependencias externas (kernel Linux)
- Cobertura completa de todas las funciones de fix activas

### 🔄 Workflow CI/CD
```yaml
Trigger: push, pull_request, workflow_dispatch
  → Checkout código
  → Setup Python 3.12
  → Ejecutar test_fixes.py
  → Reporte de resultados
```

Ver `.github/workflows/test.yml` y `TESTING.md` para más detalles.

---

## 🚀 Próximas Mejoras

- [ ] Búsqueda/filtrado en detail pages
- [ ] Exportar PDF
- [ ] API REST
- [ ] Comparación before/after
- [ ] Timeline de cambios
- [x] Integración CI/CD ✅
- [x] Tests unitarios completos ✅

---

## 💡 Ejemplos de Uso

### Ejemplo 1: Analizar linux/init y ver resultados

```bash
# Analizar
./main.py --analyze --source-dir linux/init

# Abrir dashboard en navegador
firefox html/dashboard.html

# Navegar: Analyzer → Detalle por motivo → Detalle por fichero
```

### Ejemplo 2: Aplicar fixes automáticos

```bash
# Primero analizar (si no está hecho)
./main.py --analyze --source-dir linux/init

# Aplicar fixes
./main.py --fix --json-input json/checkpatch.json

# Ver resultados
firefox html/dashboard.html

# Cambiar a tab "Autofix" para ver qué se fijó
```

### Ejemplo 3: Script completo

```bash
# Ejecutar análisis + fix + reporte
./run

# Abre automáticamente dashboard con resultados
```

---

## 📝 Notas

- Los backups (.bak) se crean automáticamente antes de aplicar fixes
- Los archivos se modifican **en lugar** (not copied)
- El dashboard es **estático** (no necesita servidor)
- Los links son URLs normales + hash (#) para deep linking
- Todo es **vanilla JavaScript** (sin jQuery, React, etc.)

---

## 🤝 Contribuciones

1. Agregar nuevo fix en `core.py`:
   ```python
   def fix_new_rule(file_path, line_number):
       """Fix description"""
       # implementation
       return True
   ```

2. Registrar en `engine.py`:
   ```python
   AUTO_FIX_RULES = {
       "your error message": fix_new_rule,
   }
   ```

3. Probar: `./test.py`

Ver ARCHITECTURE.md para más detalles.

---

## 📄 Licencia

Sistema desarrollado para análisis de kernel Linux.

---

## 👤 Autor

[@kilynho](https://github.com/kilynho)

**Versión:** 2.1  
**Estado:** Production Ready ✅  
**Última actualización:** 2024-12-05

---

## 🔗 Links Rápidos

- 🏠 [Inicio](#checkpatch---analyzer--autofix-system)
- 📊 [Reportes](#-reportes-html)
- 🔧 [Comandos](#-commandos-principales)
- 📚 [Documentación](#-documentación)
- 🐛 [Fixes](#-fixes-soportados)
- 📖 [ARCHITECTURE.md](ARCHITECTURE.md)
- 📋 [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- 📝 [CHANGELOG.md](CHANGELOG.md)

---

**¿Preguntas?** Ver documentación completa en los archivos .md del proyecto.
