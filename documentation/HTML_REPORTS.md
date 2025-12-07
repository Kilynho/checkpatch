# HTML Reports Architecture

Sistema unificado de generación de reportes HTML con separación modular.

## Estructura General

```
dashboard.html (HUB CENTRAL)
├── analyzer.html (resumen análisis)
│   ├── detail-reason.html (detalles por motivo)
│   └── detail-file.html (detalles por fichero)
└── autofix.html (resumen fixes)
    ├── autofix-detail-reason.html (detalles por tipo)
    └── autofix-detail-file.html (detalles por fichero)
```

## Archivos HTML por Sección

### ANALYZER SECTION (Análisis de Issues)

#### `analyzer.html` (41K)
**Resumen simplificado del análisis inicial**

Contenido:
- h1 título con timestamp
- h2 "Resumen global" → Tabla con:
  - Errors/Warnings totales
  - Porcentaje correcto
  - Porcentaje de issues
- h3 "Errores" → Tabla rankings por tipo
- h3 "Warnings" → Tabla rankings por tipo
- Links a detail-reason.html

Navegación:
- Clic en motivo → `detail-reason.html#id_*` (anchor link)

---

#### `detail-reason.html` (21K)
**Detalles agrupados por tipo de error/warning**

Contenido:
- h1 título
- Para cada motivo:
  - h4 header con id `id_*` (SHA1 hash de motivo)
  - Clase CSS: `errors` o `warnings` (coloreado)
  - Lista de ficheros con números de línea
  - Links a `detail-file.html#FILE:*`

Características:
- Resumen visual al inicio
- Headers agrupados alfabéticamente
- Cross-links a detail-file.html con anchors

---

#### `detail-file.html` (64K)
**Detalles expandibles por fichero**

Contenido:
- h1 título
- Para cada fichero:
  - `<details class='file-detail' id='FILE:*'>`
  - `<summary>` con nombre fichero + badges (count)
  - Lista de issues con:
    - Número línea
    - Tipo (ERROR/WARNING)
    - Mensaje truncado (100 chars)

Características:
- Secciones expandibles (HTML5 `<details>`)
- Auto-open JavaScript al acceder por hash
- Colorización: líneas con + (verde), - (rojo), # (gris)
- Scroll automático al elemento

---

### AUTOFIX SECTION (Correcciones Automáticas)

#### `autofix.html` (9K)
**Resumen simplificado de fixes aplicados**

Contenido:
- h1 título
- **Executive Summary** (NUEVO):
  - Cuadro visual: "Tasa de Éxito" (%)
  - Cuadro visual: "Ficheros Procesados" (x/y)
- h2 "Resumen global" → Tabla con:
  - Errores corregidos/saltados
  - Warnings corregidos/saltados
  - Totales
- Info box: Links a detail-reason.html y detail-file.html

Estilos:
- `.exec-summary`: Grid 2 columnas responsive
- `.exec-box`: Tarjetas con colores (éxito verde, parcial naranja)

---

#### `autofix-detail-reason.html` (3.8K)
**Detalles por tipo de fix**

Contenido:
- h1 título
- **Fix Type Summary** (NUEVO):
  - Grid de tarjetas:
    - "Tipos de Errores Fijados" → count
    - "Tipos de Warnings Fijados" → count
    - "Total de Motivos Diferentes" → count
- Para cada tipo de fix:
  - h4 header con id (SHA1 hash)
  - Clase CSS: `errors` o `warnings`
  - Lista de ficheros con líneas
  - Links a `autofix-detail-file.html#FILE:*`

Estilos:
- `.fix-type-count`: Grid responsivo de contadores
- `.fix-type-card`: Tarjetas con colores por tipo

---

#### `autofix-detail-file.html` (18K)
**Detalles expandibles por fichero (con fixes)**

Contenido:
- h1 título
- **File Summary Grid** (NUEVO):
  - Grid de tarjetas por fichero:
    - Nombre fichero (link a `#FILE:*`)
    - Contador: "✓ N" (fixed)
    - Contador: "✗ N" (skipped)
- Para cada fichero con fixes:
  - `<details class='file-detail' id='FILE:*'>`
  - `<summary>` con contador badges
  - Lista de issues:
    - Número línea
    - Badge: FIXED (verde) o SKIPPED (gris)
    - Mensaje truncado (100 chars)

Características:
- Grid responsivo de ficheros
- Auto-expand JavaScript
- Colorización FIXED/SKIPPED
- Scroll automático

Estilos:
- `.file-summary`: Grid responsive
- `.file-summary-card`: Tarjeta individual con stats

---

### DASHBOARD

#### `dashboard.html` (6.6K)
**Hub central de navegación**

Contenido:
- Header con h1 "Checkpatch Dashboard"
- Nav bar con 2 tabs: "Analyzer", "Autofix"
- Breadcrumb dinámica (breadcrumb trail)
- Iframe que carga HTML dinámicamente
- JavaScript para:
  - Gestión de rutas
  - Actualización de breadcrumb
  - Intercepción de links internos
  - Hash navigation para auto-expand

Routes definidas:
```javascript
const routes = {
  analyzer: { url: 'analyzer.html', breadcrumb: [{ label: 'Analyzer', target: 'analyzer' }] },
  autofix: { url: 'autofix.html', breadcrumb: [{ label: 'Analyzer' }, { label: 'Autofix' }] },
  'detail-reason': { url: 'detail-reason.html', breadcrumb: [{ label: 'Analyzer' }, { label: 'Detalle por motivo' }] },
  'detail-file': { url: 'detail-file.html', breadcrumb: [..., { label: 'Detalle por fichero' }] },
  'autofix-detail-reason': { url: 'autofix-detail-reason.html', breadcrumb: [..., { label: 'Detalle por tipo' }] },
  'autofix-detail-file': { url: 'autofix-detail-file.html', breadcrumb: [..., { label: 'Detalle por fichero' }] }
};
```

Características:
- Breadcrumb estado (persiste en navegación)
- Tab state management
- Link hijacking en iframe
- Auto-scroll a anchors (hash navigation)
- Responsive design

---

## Generadores en report.py

### Analyzer Section
- `generate_analyzer_html(analysis_data, html_file)` (línea 430)
- `generate_detail_reason_html(analysis_data, html_file)` (línea 636)
- `generate_detail_file_html(analysis_data, html_file)` (línea 711)

### Autofix Section
- `generate_autofix_html(fixed_data, html_file)` (línea 1045)
- `generate_autofix_detail_reason_html(fixed_data, html_file)` (línea 1135)
- `generate_autofix_detail_file_html(fixed_data, html_file)` (línea 1195)

### Dashboard
- `generate_dashboard_html(html_file)` (línea 841)

---

## Estilos Compartidos (COMMON_CSS)

Definido en `utils.py`, importado en todos los HTML:

**Colores:**
- `.errors`: Rojo (#d32f2f) + fondo rojo claro
- `.warnings`: Naranja (#f57c00) + fondo naranja claro
- `.correct`: Verde (#2e7d32)
- `.skipped`: Gris (#757575)

**Elementos:**
- `table`: Bordes, collapse, padding
- `details.file-detail`: Expandibles estilizados
- `summary`: Cursor pointer, hover effects
- `.detail-content`: Padding y background
- `.fixed-badge`: Verde con blanco
- `.skipped-badge`: Gris con blanco

**Barras:**
- `.bar`: Contenedor gris
- `.bar-inner`: Interior coloreado (errors/warnings/correct/total)

---

## Navegación y Links

### Tipos de Links:

1. **Anchor links** (dentro de misma página):
   ```html
   <a href='#FILE:abc123'>Fichero</a> → auto-expand details
   ```

2. **Cross-page links** (entre HTML):
   ```html
   <a href='detail-reason.html#id_def456'>Motivo</a> → dashboard intercept
   ```

3. **Breadcrumb links** (dashboard state):
   ```javascript
   click → navigate(target, breadcrumb_path) → update iframe
   ```

### Hash Navigation:

Al acceder a URL con hash:
```javascript
// Auto-expand: details con id=hash se abre
// Auto-scroll: elemento se scrollea a visible
```

---

## Data Flow

### From JSON to HTML:

```
json/checkpatch.json
        ↓
engine.py (analyze_file)
        ↓
report.py (generate_*_html)
        ↓
html/*.html (static files)
        ↓
dashboard.html (dynamic routing)
```

### From analyze to display:

```
checkpatch.json (por fichero/tipo)
    ↓
gen_analyzer_html() → analyzer.html (tabla resumen)
gen_detail_reason_html() → detail-reason.html (h4 por motivo)
gen_detail_file_html() → detail-file.html (details por fichero)
    ↓
dashboard.html ← intercept links → show en iframe
```

---

## Responsive Design

Todos los HTML usan:
- CSS Grid responsive (`grid-template-columns: repeat(auto-fit, minmax(...))`)
- Flexbox para layouts
- Mobile-friendly breakpoints
- Word-break para paths largos

---

## Performance Considerations

- **File sizes:**
  - analyzer.html: 41K (muchas tablas)
  - detail-file.html: 64K (expansivos detalles)
  - autofix-detail-file.html: 18K (menos issues)
  - Otros: < 10K

- **Loading:**
  - Solo se carga el HTML visible en iframe
  - Otros quedan en cache del navegador
  - Auto-expand JavaScript es eficiente

---

## Future Improvements

1. **Comparación antes/después** (side-by-side diffs)
2. **Export a PDF** con estilos
3. **API REST** para datos en JSON
4. **Búsqueda/filtrado** en detail pages
5. **Estadísticas por subsistema**
6. **Timeline de cambios**

---
