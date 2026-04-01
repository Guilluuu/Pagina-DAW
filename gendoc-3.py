import os
import html as html_lib
import urllib.parse
import threading
import socketserver
from http.server import SimpleHTTPRequestHandler
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# ---------------------------------------------------------------------------
# Directorios y parámetros globales
# ---------------------------------------------------------------------------

DIR_P3             = 'petcare-frontend'
DIR_P2             = 'other/input'
DIR_OUT_MAPAS      = 'doc/mapasDeEtiquetas'
DIR_OUT_CAPTURAS   = 'doc/capturas_responsivas'
DIR_OUT_RESPONSIVOS = 'doc/prueba-mapas-responsivos'

PUERTO = 8088

MAX_REPETICIONES = 3   # hermanos idénticos consecutivos antes de colapsar

# Configuración de los mapas de layout responsivo
CONFIGS_RESPONSIVOS = {
    'desktop': {'viewport': {'width': 1440, 'height': 900},  'canvas_w': 800},
    'mobile':  {'viewport': {'width': 390,  'height': 844},  'canvas_w': 390},
}
MAX_CANVAS_HEIGHT = 12_000   # px — techo razonable para la imagen de salida

ETIQUETAS_BLOQUE = {
    'main', 'header', 'footer', 'nav', 'aside', 'section', 'article',
    'div', 'form', 'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td',
    'ul', 'ol', 'li', 'dl', 'dt', 'dd', 'figure', 'figcaption', 'details',
    'dialog', 'address', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p',
    'blockquote', 'fieldset', 'legend', 'search', 'menu'
}

ETIQUETAS_ELIMINAR = {
    'head', 'script', 'style', 'meta', 'link', 'noscript', 'template',
    'iframe', 'object', 'embed', 'svg', 'canvas', 'video', 'audio', 'img'
}

ESTILOS_BOXMODEL = """
    head, meta, title, link, script, style, img, svg { display: none !important; }
    body { font-family: monospace; background: #f4f4f4; padding: 20px; margin: 0; }

    *[data-etiqueta] {
        border: 2px solid #2c3e50;
        padding: 10px;
        margin: 10px;
        display: block;
        background: white;
        position: relative;
        min-height: 20px;
    }
    *[data-etiqueta]::before {
        content: attr(data-etiqueta);
        display: block;
        background: #2c3e50;
        color: white;
        padding: 4px 8px;
        font-size: 14px;
        font-weight: bold;
        width: fit-content;
        margin-bottom: 8px;
    }

    /* Placeholder de elementos colapsados */
    *[data-placeholder] {
        border: 2px dashed #95a5a6 !important;
        background: #ecf0f1 !important;
        margin: 6px 10px;
        padding: 6px 12px;
        display: block;
    }
    *[data-placeholder]::before {
        content: "\\2026  +" attr(data-placeholder) " elementos mas con la misma estructura";
        display: block;
        background: none !important;
        color: #7f8c8d;
        font-size: 13px;
        font-style: italic;
        font-weight: normal !important;
        margin-bottom: 0 !important;
    }
"""

# JavaScript inyectado en la página real para extraer posiciones del DOM renderizado.
# Devuelve una lista de objetos con las coordenadas absolutas y metadatos de cada
# elemento de bloque visible, ordenados de menor a mayor profundidad (padres primero).
JS_EXTRAE_LAYOUT = """() => {
    const TAGS = new Set([
        'main','header','footer','nav','aside','section','article',
        'div','form','table','thead','tbody','tr','th','td',
        'ul','ol','li','dl','dt','dd',
        'figure','figcaption','details','dialog','address',
        'h1','h2','h3','h4','h5','h6','p','blockquote',
        'fieldset','legend','search','menu'
    ]);

    function profundidad(el) {
        let d = 0, cur = el.parentElement;
        while (cur && cur !== document.body) { d++; cur = cur.parentElement; }
        return d;
    }

    const nodos = document.querySelectorAll([...TAGS].join(','));
    const scrollX = window.pageXOffset || 0;
    const scrollY = window.pageYOffset || 0;
    const resultados = [];

    for (const el of nodos) {
        const st = window.getComputedStyle(el);
        if (st.display === 'none' || st.visibility === 'hidden'
                || parseFloat(st.opacity) < 0.05) continue;

        const r = el.getBoundingClientRect();
        if (r.width < 4 || r.height < 4) continue;

        resultados.push({
            tag:     el.tagName.toLowerCase(),
            id:      el.id || null,
            classes: [...el.classList].slice(0, 4),
            x:       r.left + scrollX,
            y:       r.top  + scrollY,
            w:       r.width,
            h:       r.height,
            depth:   profundidad(el)
        });
    }

    // Padres primero → los hijos se pintan encima (z-index mayor)
    resultados.sort((a, b) => a.depth - b.depth || a.y - b.y);
    return resultados;
}"""


# ---------------------------------------------------------------------------
# Servidor HTTP
# ---------------------------------------------------------------------------

class ManejadorSilencioso(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

class ServidorTCPReutilizable(socketserver.TCPServer):
    allow_reuse_address = True


# ---------------------------------------------------------------------------
# Transformaciones del árbol HTML (mapa de cajas clásico)
# ---------------------------------------------------------------------------

def limpiar_y_preparar_arbol(soup):
    for tag in soup.find_all(list(ETIQUETAS_ELIMINAR)):
        tag.decompose()
    for tag in reversed(soup.find_all(True)):
        if tag.name not in ETIQUETAS_BLOQUE and tag.name not in ['html', 'body']:
            if tag.parent is not None:
                tag.unwrap()


def limpiar_atributos_html(soup):
    """Conserva únicamente 'id' y 'class'; elimina el resto."""
    for tag in soup.find_all(True):
        borrar = [a for a in tag.attrs if a not in ('id', 'class')]
        for a in borrar:
            del tag[a]


def normalizar_clases(soup):
    """Convierte class=['c1','c2'] → data-clases='.c1.c2' y elimina class."""
    for tag in soup.find_all(True):
        clases = tag.get('class')
        if clases:
            tag['data-clases'] = '.' + '.'.join(clases)
            del tag['class']


def estructura_elemento(tag):
    """Firma estructural recursiva basada solo en nombres de etiqueta."""
    if not hasattr(tag, 'name') or tag.name is None:
        return None
    hijos = tuple(
        estructura_elemento(c)
        for c in tag.children
        if hasattr(c, 'name') and c.name is not None and not c.get('data-placeholder')
    )
    return (tag.name, hijos)


def colapsar_repetidos(soup, max_rep=MAX_REPETICIONES):
    """Colapsa hermanos consecutivos con la misma estructura en un marcador."""
    for parent in soup.find_all(True):
        hijos = [
            c for c in parent.children
            if hasattr(c, 'name') and c.name is not None and not c.get('data-placeholder')
        ]
        i = 0
        while i < len(hijos):
            firma = estructura_elemento(hijos[i])
            j = i + 1
            while (j < len(hijos)
                   and not hijos[j].get('data-placeholder')
                   and estructura_elemento(hijos[j]) == firma):
                j += 1

            if j - i > max_rep:
                excedente = j - i - max_rep
                for elem in hijos[i + max_rep:j]:
                    elem.decompose()
                placeholder = soup.new_tag('div')
                placeholder['data-placeholder'] = str(excedente)
                hijos[i + max_rep - 1].insert_after(placeholder)
                hijos = [c for c in parent.children
                         if hasattr(c, 'name') and c.name is not None]
                i = i + max_rep + 1
            else:
                i = j


def aplicar_formato_cajas(soup):
    """Convierte cada etiqueta en un <div data-etiqueta="tag [#id] [.cls]">."""
    for tag in soup.find_all(True):
        if tag.name in ['html', 'body']:
            continue
        if tag.get('data-placeholder') is not None:
            continue
        label = tag.name
        if tag.get('id'):
            label += f' #{tag["id"]}'
        if tag.get('data-clases'):
            label += f' {tag["data-clases"]}'
        tag['data-etiqueta'] = label
        tag.name = 'div'
        for nodo in tag.find_all(string=True, recursive=False):
            if nodo.strip():
                nodo.extract()


# ---------------------------------------------------------------------------
# Captura con Playwright
# ---------------------------------------------------------------------------

def navegar(page, ruta_relativa, viewport=None):
    """Navega a ruta_relativa a través del servidor HTTP local."""
    page.set_viewport_size(viewport or {'width': 1280, 'height': 800})
    ruta_url = urllib.parse.quote(ruta_relativa.replace('\\', '/'))
    page.goto(f"http://localhost:{PUERTO}/{ruta_url}", wait_until='networkidle')


def capturar_pantalla(page, ruta_relativa, ruta_salida,
                       viewport=None, full_page=True, ajustar_body=False):
    navegar(page, ruta_relativa, viewport)
    if ajustar_body:
        page.locator('body').screenshot(path=ruta_salida)
    else:
        page.screenshot(path=ruta_salida, full_page=full_page)


def obtener_html_renderizado(page, directorio, archivo):
    """Retorna el HTML completamente renderizado (JS ejecutado)."""
    navegar(page, os.path.join(directorio, archivo))
    return page.content()


# ---------------------------------------------------------------------------
# Generación: mapa de cajas clásico
# ---------------------------------------------------------------------------

def generar_mapas(archivo, page, directorio, sufijo_salida=''):
    """
    Pipeline del mapa de cajas:
      DOM renderizado → limpieza → normalización → colapso → cajas → captura

    Salida:  {nombre}-boxmodel.png          (antiguo)
             {nombre}-boxmodel-new.png      (actual)
    """
    nombre_base = archivo.replace('.html', '')
    soup = BeautifulSoup(obtener_html_renderizado(page, directorio, archivo), 'html.parser')

    limpiar_y_preparar_arbol(soup)
    limpiar_atributos_html(soup)
    normalizar_clases(soup)
    colapsar_repetidos(soup)
    aplicar_formato_cajas(soup)

    estilo = soup.new_tag('style')
    estilo.string = ESTILOS_BOXMODEL
    if not soup.head:
        soup.insert(0, soup.new_tag('head'))
    soup.head.append(estilo)

    ruta_tmp = os.path.join(DIR_OUT_MAPAS, f"{nombre_base}_tmp.html")
    with open(ruta_tmp, 'w', encoding='utf-8') as f:
        f.write(str(soup))

    capturar_pantalla(page, ruta_tmp,
                      os.path.join(DIR_OUT_MAPAS, f"{nombre_base}-boxmodel{sufijo_salida}.png"),
                      ajustar_body=True)
    os.remove(ruta_tmp)


# ---------------------------------------------------------------------------
# Generación: mapas de layout responsivo
# ---------------------------------------------------------------------------

def _construir_html_layout(elementos, page_height, viewport_w, canvas_w):
    """
    Genera un documento HTML con los elementos posicionados de forma absoluta
    a escala, replicando visualmente el layout real del navegador.

    - Los elementos se ordenan por profundidad (padres primero) y se les
      asigna z-index creciente, de modo que los hijos aparecen sobre los padres.
    - El fondo de cada caja varía ligeramente con la profundidad para facilitar
      la lectura del anidamiento.
    - La etiqueta muestra: nombre_tag [#id] [.clases]
    """
    escala     = canvas_w / viewport_w
    canvas_h   = min(int(page_height * escala), MAX_CANVAS_HEIGHT)
    limite_y   = MAX_CANVAS_HEIGHT / escala   # elementos por debajo se omiten

    # Paleta de fondos por profundidad (cíclica)
    fondos = [
        'rgba(255,255,255,0.55)',
        'rgba(240,248,255,0.60)',
        'rgba(255,250,240,0.60)',
        'rgba(240,255,240,0.60)',
        'rgba(255,240,255,0.60)',
    ]

    divs = []
    for el in elementos:
        if el['y'] > limite_y:
            continue
        x = el['x'] * escala
        y = el['y'] * escala
        w = el['w'] * escala
        h = el['h'] * escala
        if w < 4 or h < 4:
            continue

        depth  = el.get('depth', 0)
        z      = depth + 1
        fondo  = fondos[depth % len(fondos)]

        label = el['tag']
        if el.get('id'):
            label += f' #{el["id"]}'
        if el.get('classes'):
            label += ' .' + '.'.join(el['classes'])
        label = html_lib.escape(label)

        # Borde ligeramente más claro a mayor profundidad
        alpha  = max(0.3, 0.9 - depth * 0.08)
        borde  = f'rgba(44,62,80,{alpha:.2f})'

        divs.append(
            f'<div class="e" style="left:{x:.1f}px;top:{y:.1f}px;'
            f'width:{w:.1f}px;height:{h:.1f}px;z-index:{z};'
            f'border-color:{borde};background:{fondo};">'
            f'<span class="l">{label}</span></div>'
        )

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{
  position:relative;
  width:{canvas_w}px;
  height:{canvas_h}px;
  background:#eef0f3;
  font-family:monospace;
  overflow:hidden;
}}
.e{{
  position:absolute;
  border:1.5px solid;
}}
.l{{
  display:inline-block;
  background:#2c3e50;
  color:#fff;
  font-size:9px;
  font-weight:bold;
  padding:1px 3px;
  line-height:1.4;
  white-space:nowrap;
  overflow:hidden;
  text-overflow:ellipsis;
  max-width:100%;
  pointer-events:none;
}}
</style>
</head>
<body>
{''.join(divs)}
</body>
</html>"""


def generar_mapa_responsivo(archivo, page, directorio):
    """
    Para cada viewport (desktop / móvil):
      1. Navega a la página real con ese viewport y espera networkidle.
      2. Extrae las posiciones absolutas renderizadas de todos los elementos
         de bloque visibles mediante getBoundingClientRect() en JS.
      3. Genera un HTML escalado con los elementos en position:absolute.
      4. Captura el HTML generado con Playwright → PNG.

    Los archivos originales no se modifican en ningún momento.

    Salida:  {nombre}-layout-desktop.png
             {nombre}-layout-mobile.png
    """
    nombre_base = archivo.replace('.html', '')

    for disp, cfg in CONFIGS_RESPONSIVOS.items():
        vp = cfg['viewport']
        canvas_w = cfg['canvas_w']

        # 1. Navegar a la página real con el viewport correspondiente
        navegar(page, os.path.join(directorio, archivo), viewport=vp)

        # 2. Extraer posiciones del DOM renderizado
        elementos  = page.evaluate(JS_EXTRAE_LAYOUT)
        page_height = page.evaluate(
            "() => Math.max(document.body.scrollHeight,"
            " document.documentElement.scrollHeight)"
        )

        # 3. Construir HTML de layout escalado
        html_layout = _construir_html_layout(elementos, page_height, vp['width'], canvas_w)

        ruta_tmp = os.path.join(DIR_OUT_RESPONSIVOS, f"{nombre_base}_{disp}_tmp.html")
        with open(ruta_tmp, 'w', encoding='utf-8') as f:
            f.write(html_layout)

        # 4. Renderizar el HTML generado y capturar
        escala    = canvas_w / vp['width']
        canvas_h  = min(int(page_height * escala), MAX_CANVAS_HEIGHT)
        # Viewport ajustado al canvas para que body.screenshot lo capture completo
        page.set_viewport_size({'width': canvas_w + 40, 'height': min(canvas_h + 40, 16_000)})
        ruta_url  = urllib.parse.quote(ruta_tmp.replace('\\', '/'))
        page.goto(f"http://localhost:{PUERTO}/{ruta_url}", wait_until='domcontentloaded')

        ruta_salida = os.path.join(DIR_OUT_RESPONSIVOS, f"{nombre_base}-layout-{disp}.png")
        page.locator('body').screenshot(path=ruta_salida)
        os.remove(ruta_tmp)

        print(f"    → layout {disp}: {ruta_salida}")


# ---------------------------------------------------------------------------
# Capturas responsivas reales
# ---------------------------------------------------------------------------

def generar_capturas_reales_responsivas(archivo, page, directorio):
    """
    Capturas de pantalla reales a tres viewports estándar.
    full_page=False → imagen con exactamente las dimensiones del viewport.
    Solo se usa para archivos actuales (petcare-frontend).
    """
    nombre_base = archivo.replace('.html', '')
    ruta_relativa = os.path.join(directorio, archivo)

    dispositivos = {
        'desktop': {'width': 1440, 'height': 900},
        'tablet':  {'width': 768,  'height': 1024},
        'mobile':  {'width': 390,  'height': 844},
    }
    for disp, vp in dispositivos.items():
        capturar_pantalla(
            page, ruta_relativa,
            os.path.join(DIR_OUT_CAPTURAS, f"{nombre_base}-{disp}.png"),
            viewport=vp, ajustar_body=False, full_page=False
        )


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    for d in (DIR_OUT_MAPAS, DIR_OUT_CAPTURAS, DIR_OUT_RESPONSIVOS):
        os.makedirs(d, exist_ok=True)

    print(f"Iniciando servidor local en el puerto {PUERTO}...")
    httpd = ServidorTCPReutilizable(("", PUERTO), ManejadorSilencioso)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # ── 1. Mapas de cajas "antiguos" (other/input) ──────────────────────
        for archivo in sorted(f for f in os.listdir(DIR_P2) if f.endswith('.html')):
            print(f"[antiguo] {archivo}...")
            generar_mapas(archivo, page, DIR_P2, sufijo_salida='')

        # ── 2. Archivos actuales (petcare-frontend) ──────────────────────────
        for archivo in sorted(f for f in os.listdir(DIR_P3) if f.endswith('.html')):
            print(f"[actual]  {archivo}...")
            generar_mapas(archivo, page, DIR_P3, sufijo_salida='-new')
            generar_capturas_reales_responsivas(archivo, page, DIR_P3)
            generar_mapa_responsivo(archivo, page, DIR_P3)

        browser.close()

    httpd.shutdown()
    httpd.server_close()
    print("\n¡Proceso completado con éxito! Revisa la carpeta doc/")
