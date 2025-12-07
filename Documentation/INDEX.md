# Project Index & Navigation Map

Mapa completo del proyecto con guía de navegación.

## 📑 Documentación

### Por Tipo de Usuario

#### 👤 Usuario Final (quiere usar el sistema)
1. **START HERE:** [README.md](README.md)
   - ¿Qué es esto?
   - Inicio rápido (5 minutos)
   - Ejemplos de uso

2. **QUICK GUIDE:** [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
   - URLs de acceso
   - Contenido de cada página HTML
   - Colores y significado

3. **SEE RESULTS:** Abrir `html/dashboard.html` en navegador

#### 👨‍💻 Developer (quiere entender/modificar)
1. **START HERE:** [ARCHITECTURE.md](ARCHITECTURE.md)
   - Estructura de módulos
   - Flujo de datos
   - Diseño general

2. **DEEP DIVE:** [HTML_REPORTS.md](HTML_REPORTS.md)
   - Arquitectura de 7 reportes
   - Sistema de navegación
   - Generadores de cada página

3. **CHANGELOG:** [CHANGELOG.md](CHANGELOG.md)
   - Qué cambió recientemente
   - Versión actual (2.1)
   - Roadmap futuro

4. **CODE:** Ver comentarios en archivos `.py`

#### 🔍 Analista (quiere ver issues encontrados)
1. **QUICK REFERENCE:** [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
2. **Abrir:** `html/dashboard.html` → pestaña "Analyzer"
3. **Navegar:** 
   - Click motivo → ver todos los archivos con ese error
   - Click archivo → ver detalles línea por línea

#### 🛠️ QA/Testing (quiere ver fixes aplicados)
1. **QUICK REFERENCE:** [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
2. **Abrir:** `html/dashboard.html` → pestaña "Autofix"
3. **Ver:** Tasa de éxito + archivos modificados
4. **Verificar:** diff vs backups (.bak)

---

## 🗂️ Estructura de Archivos

### Documentación (7 archivos .md, ~1700 líneas)
```
README.md                   [450 líneas]    ← EMPEZAR AQUÍ
├─ Inicio rápido
├─ Estructura proyecto
├─ Características
├─ Estadísticas
└─ Links a otros docs

ARCHITECTURE.md             [254 líneas]    ← Developers
├─ Módulos Python
├─ Flujo de datos
├─ Datos del sistema
└─ Estadísticas

HTML_REPORTS.md             [300 líneas]    ← HTML Structure
├─ 7 reportes descripción
├─ Data flow
├─ Navegación
└─ Performance

QUICK_REFERENCE.md          [180 líneas]    ← Cheat sheet
├─ URLs acceso
├─ Contenido páginas
├─ Números actuales
└─ Tabla generadores

CHANGELOG.md                [220 líneas]    ← Historia
├─ v2.1 (actual)
├─ v2.0 (anterior)
├─ Fixes y mejoras
└─ Roadmap

QUICK_START.md (este)       [~300 líneas]   ← Mapeo
└─ Este archivo

FIXES_STATUS.md             [~150 líneas]   ← Referencia
└─ Estado de cada fix

FALSOS_POSITIVOS...md       [~100 líneas]   ← Análisis
└─ False positives encontrados

COMPILATION_TROUBLESHOOTING.md  [~250 líneas]   ← Compilación
├─ Error classification
├─ Common errors & solutions
├─ Kernel configuration
└─ Bug reporting
```

#### 🔧 Troubleshooter (errores de compilación)
1. **START HERE:** [COMPILATION_TROUBLESHOOTING.md](COMPILATION_TROUBLESHOOTING.md)
2. **Check:** Clasificación de errores en consola/JSON
3. **Fix:**
   - `[config]` → Problema de configuración kernel
   - `[code]` → Bug real (verificar diff)
   - `[dependency]` → Headers/includes faltantes
4. **Verify:** Compilar archivo original sin modificaciones

### Python (7 módulos, ~2000 líneas)
```
main.py                     [336 líneas]    Entry point
├─ analyze_mode()
├─ fix_mode()
└─ --analyze, --fix, --dry-run

engine.py                   [209 líneas]    Core logic
├─ analyze_file()
├─ apply_fixes()
└─ AUTO_FIX_RULES dict

core.py                     [750 líneas]    Fix implementations
├─ fix_*() functions (40+)
└─ Regex patterns

report.py                   [1289 líneas]   HTML generation
├─ generate_analyzer_html()
├─ generate_autofix_html()
├─ generate_dashboard_html()
└─ 7 generators total

utils.py                    [83 líneas]     Utilities
├─ find_source_files()
├─ backup_read()
└─ Pattern transforms

constants.py                [54 líneas]     Constants
└─ Pattern/replacement tuples

test.py                     [201 líneas]    Unit tests
└─ Integration tests
```

### HTML Reports (7 archivos, ~180K)
```
dashboard.html              [6.6K]          🏠 Hub central
├─ Tabs: Analyzer, Autofix
├─ Breadcrumb navigation
└─ Iframe viewer

ANALYZER SECTION:
├─ analyzer.html             [41K]          📊 Resumen
├─ detail-reason.html        [21K]          🔍 Por tipo
└─ detail-file.html          [64K]          📄 Por fichero

AUTOFIX SECTION:
├─ autofix.html              [9K]           ✨ Resumen
├─ autofix-detail-reason.html [3.8K]        🎯 Por tipo
└─ autofix-detail-file.html   [18K]         🔧 Por fichero
```

### Data (JSON)
```
json/
├─ checkpatch.json          [24K]           All issues found
└─ fixed.json               [27K]           Fix results
```

### Generated Backups
```
__pycache__/                                Python cache (ignore)
*/.bak                                      File backups (if autofix run)
```

---

## 🔗 Relaciones entre Documentos

```
README.md (overview)
├─ Enlaza → ARCHITECTURE.md (technical)
├─ Enlaza → QUICK_REFERENCE.md (quick tips)
├─ Enlaza → CHANGELOG.md (history)
├─ Enlaza → HTML_REPORTS.md (details)
└─ Enlaza → FILES (código)

ARCHITECTURE.md
├─ Describe módulos
├─ Enlaza → HTML_REPORTS.md
└─ Enlaza → CODE

HTML_REPORTS.md
├─ Describe 7 reportes
├─ Enlaza → Dashboard routes
└─ Enlaza → CSS classes

QUICK_REFERENCE.md
├─ URLs rápidas
├─ Resumen de contenidos
└─ Links a generadores

CHANGELOG.md
├─ v2.1: 3 nuevos generadores
├─ v2.0: Refactor unificado
└─ Future roadmap
```

---

## 🎯 Guías por Tarea

### Tarea: Analizar archivos
```
1. Leer: README.md "Inicio Rápido"
2. Ejecutar: ./main.py --analyze --source-dir linux/init
3. Ver: html/dashboard.html → Analyzer tab
4. Referencia: QUICK_REFERENCE.md
```

### Tarea: Aplicar fixes automáticos
```
1. Leer: README.md "Uso Básico" → fix mode
2. Ejecutar: ./main.py --fix --json-input json/checkpatch.json
3. Ver: html/dashboard.html → Autofix tab
4. Verify: Archivos modificados + backups .bak
5. Referencia: CHANGELOG.md → fix types soportados
```

### Tarea: Añadir nuevo fix
```
1. Leer: ARCHITECTURE.md "Contribuciones"
2. Ver: core.py (ejemplos de otros fixes)
3. Implementar: fix_new_rule() en core.py
4. Registrar: AUTO_FIX_RULES en engine.py
5. Test: ./test.py
6. Documento: FIXES_STATUS.md
```

### Tarea: Entender dashboard
```
1. Leer: QUICK_REFERENCE.md
2. Leer: HTML_REPORTS.md "Dashboard"
3. Abrir: html/dashboard.html
4. Prueba: Clickear tabs, breadcrumbs, links
5. Check hash: Abrir console (F12), ver navegación
```

### Tarea: Debuggear HTML generation
```
1. Leer: ARCHITECTURE.md "report.py"
2. Leer: HTML_REPORTS.md
3. Ver código: report.py línea 1045+ (generadores)
4. Editar: Función específica
5. Test: ./main.py --analyze (y abrir html)
```

---

## 📊 Estadísticas del Proyecto

### Tamaño
- **Python:** ~2000 líneas (7 módulos)
- **HTML:** ~180K (7 reportes)
- **Documentación:** ~1700 líneas (7 archivos)
- **Total:** ~3.9K líneas + archivos HTML

### Cobertura
- **Fixes soportados:** 40+
- **Error types:** 50+
- **Archivos analizados:** 14 (linux/init/)
- **Current test dataset:** 168 issues

### Performance
- **Análisis:** ~0.5s por archivo
- **Autofix:** ~1-2s por archivo
- **HTML gen:** ~0.1s por reporte
- **Total:** ~20-30s para dataset completo

---

## 🔍 Buscar por Concepto

### Si necesitas... busca en:

- **"¿Qué es checkpatch?"** → README.md intro
- **"Cómo analizar"** → README.md quick start
- **"Cómo fixear"** → README.md fix section
- **"Arquitectura"** → ARCHITECTURE.md
- **"HTML structure"** → HTML_REPORTS.md
- **"Qué generadores"** → QUICK_REFERENCE.md
- **"Cambios recientes"** → CHANGELOG.md
- **"Estado de fixes"** → FIXES_STATUS.md
- **"False positives"** → FALSOS_POSITIVOS...md
- **"Cómo agregar fix"** → ARCHITECTURE.md contribuciones
- **"URLs de reportes"** → QUICK_REFERENCE.md
- **"Colores significado"** → QUICK_REFERENCE.md
- **"Dashboard navigation"** → HTML_REPORTS.md o QUICK_REFERENCE.md

---

## 🚀 Comandos Rápidos

```bash
# Ver documentación
cat README.md              # Inicio general
cat QUICK_REFERENCE.md    # Guía rápida

# Ejecutar sistema
./main.py --analyze --source-dir linux/init
./main.py --fix --json-input json/checkpatch.json
./run                     # Todo automatizado

# Tests
./test.py
./test.py TestAutofix.test_indent

# Ver reportes
firefox html/dashboard.html
open html/dashboard.html        # macOS
start html/dashboard.html       # Windows

# Verificación
python3 -m py_compile *.py
```

---

## 📚 Lectura Recomendada

### Orden de lectura por caso:

**Caso 1: "Quiero usar esto ahora"**
1. README.md (5 min)
2. ./main.py --analyze --source-dir linux/init (2 min)
3. Abrir html/dashboard.html
4. QUICK_REFERENCE.md si necesito ayuda

**Caso 2: "Necesito entender el código"**
1. ARCHITECTURE.md (10 min)
2. HTML_REPORTS.md (5 min)
3. Código: engine.py → core.py → report.py (30 min)
4. Ver test.py para ejemplos

**Caso 3: "Necesito agregar un fix"**
1. ARCHITECTURE.md "Contribuciones"
2. FIXES_STATUS.md (para ver qué existe)
3. core.py (ver ejemplos similares)
4. Implementar + test.py

**Caso 4: "¿Qué cambió recientemente?"**
1. CHANGELOG.md
2. Buscar versión relevante
3. ARCHITECTURE.md para detalles

---

## ✅ Checklist: Primera Vez

- [ ] Clonar repo
- [ ] `chmod +x main.py test.py run`
- [ ] Leer README.md
- [ ] Ejecutar `./main.py --analyze --source-dir linux/init`
- [ ] Abrir `html/dashboard.html` en navegador
- [ ] Clickear tabs y links para explorar
- [ ] Ejecutar `./main.py --fix --json-input json/checkpatch.json`
- [ ] Abrir dashboard nuevamente (se actualizó)
- [ ] Ver tab "Autofix" para resultados
- [ ] Leer QUICK_REFERENCE.md para tips

---

## 🐞 Si Algo Falla

1. **No se genera HTML?** → Ver console: `./main.py --analyze`
2. **Links rotos?** → Check QUICK_REFERENCE.md URLs
3. **¿Código Python error?** → `python3 -m py_compile *.py`
4. **¿HTML no abre?** → Asegurar ruta: `file:///home/kilynho/src/checkpatch/html/dashboard.html`
5. **¿No hay datos?** → Revisar: `json/checkpatch.json` existe?

---

## 📞 Ayuda Rápida

```
Error                          | Solución
-------------------------------|----------------------------------
"No .html files found"         | Ejecutar --analyze primero
"Invalid JSON"                 | Revisar json/checkpatch.json
"FileNotFoundError"            | Usar ruta absoluta
"checkpatch.pl not found"      | Instalar checkpatch.pl
Links no funcionan             | Usar file:// protocol completo
Dashboard en blanco            | Verificar CORS (abrir local ok)
Fixes no se aplican            | Usar --fix (no --analyze)
```

---

**Última actualización:** 2024-12-05  
**Versión:** 2.1  
**Estado:** ✅ Production Ready

*Para preguntas, ver sección relevante arriba o archivo específico recomendado.*
