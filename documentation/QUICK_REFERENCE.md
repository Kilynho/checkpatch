# Quick Reference - Reportes HTML

## Estructura Actual

```
DASHBOARD.HTML (Portal principal)
    │
    ├─→ ANALYZER TAB
    │   ├─ analyzer.html (resumen)
    │   ├─ detail-reason.html (por tipo)
    │   └─ detail-file.html (por fichero expandible)
    │
    └─→ AUTOFIX TAB
        ├─ autofix.html (resumen + executive boxes)
        ├─ autofix-detail-reason.html (por tipo + cards)
        └─ autofix-detail-file.html (por fichero + grid)
```

## Archivos Generados

| Archivo | Tamaño | Generador | Propósito |
|---------|--------|-----------|----------|
| `dashboard.html` | 6.6K | `generate_dashboard_html()` | Hub navegación |
| `analyzer.html` | 41K | `generate_analyzer_html()` | Resumen análisis |
| `detail-reason.html` | 21K | `generate_detail_reason_html()` | Detalles por tipo |
| `detail-file.html` | 64K | `generate_detail_file_html()` | Detalles fichero |
| `autofix.html` | 9K | `generate_autofix_html()` | Resumen fixes ⭐ |
| `autofix-detail-reason.html` | 3.8K | `generate_autofix_detail_reason_html()` | Detalles tipo ⭐ |
| `autofix-detail-file.html` | 18K | `generate_autofix_detail_file_html()` | Detalles fichero ⭐ |

⭐ = Generadores nuevos (últimas 3 sesiones)

## URLs de Acceso

```
Local browser:
  file:///home/kilynho/src/checkpatch/html/dashboard.html

Rutas disponibles:
  #/analyzer → analyzer.html
  #/autofix → autofix.html
  #/detail-reason → detail-reason.html
  #/detail-file → detail-file.html
  #/autofix-detail-reason → autofix-detail-reason.html
  #/autofix-detail-file → autofix-detail-file.html

Hash navigation (auto-expand):
  analyzer.html#id_XYZ → auto-open motivo en detail-reason.html
  detail-reason.html#FILE:ABC → auto-open fichero en detail-file.html
  (Similar para autofix)
```

## Generación de Reportes

### Modo Análisis
```bash
./main.py --analyze --source-dir linux/init
```
Genera:
- `analyzer.html` ✅
- `detail-reason.html` ✅
- `detail-file.html` ✅
- `dashboard.html` ✅
- `json/checkpatch.json` ✅

### Modo Autofix
```bash
./main.py --fix --json-input json/checkpatch.json
```
Genera:
- `autofix.html` ✅
- `autofix-detail-reason.html` ✅
- `autofix-detail-file.html` ✅
- `json/fixed.json` ✅

## Contenido por Página

### analyzer.html
- ✔ Título + timestamp
- ✔ Tabla "Resumen Global" (stats)
- ✔ Tabla "Errores" (top 10 por frecuencia)
- ✔ Tabla "Warnings" (top 10 por frecuencia)
- ✔ Links: clic en motivo → `detail-reason.html#id_*`

### detail-reason.html
- ✔ Título + resumen visual
- ✔ h4 headers por cada motivo (h4 id=`id_*`)
- ✔ Clase CSS: `.errors` (rojo) o `.warnings` (naranja)
- ✔ Lista: ficheros + números línea
- ✔ Links: clic en fichero → `detail-file.html#FILE:*`

### detail-file.html
- ✔ Título + contador fichas
- ✔ Para cada fichero: `<details id='FILE:*'>`
- ✔ Auto-expand si viene de hash (`#FILE:*`)
- ✔ Lista: número línea + tipo + mensaje
- ✔ Colorización: línea con + = verde, - = rojo, # = gris
- ✔ JavaScript: auto-scroll + auto-expand

### autofix.html ⭐
- ✔ Título + timestamp
- ✔ **EXECUTIVE SUMMARY** (NEW):
  - Cuadro: "Tasa de Éxito" (%)
  - Cuadro: "Ficheros Procesados" (x/y)
- ✔ Tabla "Resumen Global" (stats)
- ✔ Links a detail pages

### autofix-detail-reason.html ⭐
- ✔ Título
- ✔ **FIX-TYPE CARDS** (NEW):
  - Grid: "Tipos Errores Fijados"
  - Grid: "Tipos Warnings Fijados"
  - Grid: "Total de Motivos"
- ✔ h4 headers por tipo de fix
- ✔ Clase CSS: `.errors` (rojo) o `.warnings` (naranja)
- ✔ Links: clic en fichero → `autofix-detail-file.html#FILE:*`

### autofix-detail-file.html ⭐
- ✔ Título
- ✔ **FILE-SUMMARY GRID** (NEW):
  - Card por fichero: "✓ N" + "✗ N" + link
- ✔ Para cada fichero: `<details id='FILE:*'>`
- ✔ Auto-expand + auto-scroll
- ✔ Lista: número línea + badge (FIXED verde / SKIPPED gris) + mensaje

### dashboard.html
- ✔ Header "Checkpatch Dashboard"
- ✔ Nav bar: 2 tabs (Analyzer, Autofix)
- ✔ Breadcrumb dinámico
- ✔ Iframe viewer
- ✔ JavaScript: route handling + link hijacking

## CSS Classes Nuevas

### autofix.html
- `.exec-summary`: Grid 2-col responsivo
- `.exec-box`: Tarjeta con color (verde éxito, naranja parcial)

### autofix-detail-reason.html
- `.fix-type-count`: Grid responsivo contadores
- `.fix-type-card`: Tarjeta individual

### autofix-detail-file.html
- `.file-summary`: Grid responsivo ficheros
- `.file-summary-card`: Tarjeta individual con stats

## Colores

```css
/* Colores heredados (COMMON_CSS) */
.errors    → Rojo #d32f2f + fondo rojo claro
.warnings  → Naranja #f57c00 + fondo naranja claro
.correct   → Verde #2e7d32
.skipped   → Gris #757575

/* Elementos específicos */
summary    → Cursor pointer, hover highlight
details    → Expandible, auto-open en hash
.bar       → Barra progreso gris
.bar-inner → Interior coloreado
```

## Números Actuales

- **Total issues analizados**: 168
- **Issues corregidos**: 9 (5.4%)
- **Issues saltados**: 159 (94.6%)
- **Ficheros procesados**: 3/12 (25%)
- **Razones diferentes**: 8 tipos de fixes

## Pasos Siguientes

1. ✅ Analyzer section modularizado (3 files)
2. ✅ Autofix section modularizado (3 files)
3. ✅ Dashboard con 6 rutas
4. ⏳ **Documentación** (en progreso)
   - HTML_REPORTS.md (nueva)
   - ARCHITECTURE.md (actualizado)
   - Este archivo (QUICK_REFERENCE.md)
5. 🔮 Futuro:
   - Búsqueda/filtrado
   - Exportar PDF
   - API REST
   - Comparación antes/después
