import os
import urllib.parse
import threading
import socketserver
from http.server import SimpleHTTPRequestHandler
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# Configuración de directorios y servidor
DIR_P3 = 'petcare-frontend'
DIR_P2 = 'other/input'
DIR_OUT_MAPAS = 'doc/mapasDeEtiquetas'
DIR_OUT_CAPTURAS = 'doc/capturas_responsivas'
PUERTO = 8088

MAX_REPETICIONES = 3   # Máximo de hermanos con la misma estructura antes de colapsar

# Parámetros de URL que deben añadirse a páginas de detalle para que carguen
# contenido real. Solo se aplican a los archivos actuales (DIR_P3).
PARAMS_URL_DETALLE = {
    'servicio-especifico.html': '?id=neurologia',
    'consejo-especifico.html':  '?id=consejo-perro-01',
}

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


# ---------------------------------------------------------------------------
# Servidor HTTP
# ---------------------------------------------------------------------------

class ManejadorSilencioso(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

class ServidorTCPReutilizable(socketserver.TCPServer):
    allow_reuse_address = True


# ---------------------------------------------------------------------------
# Transformaciones del árbol HTML
# ---------------------------------------------------------------------------

def limpiar_y_preparar_arbol(soup):
    """Elimina etiquetas no estructurales y desenvuelve las etiquetas inline."""
    for tag in soup.find_all(list(ETIQUETAS_ELIMINAR)):
        tag.decompose()

    for tag in reversed(soup.find_all(True)):
        if tag.name not in ETIQUETAS_BLOQUE and tag.name not in ['html', 'body']:
            if tag.parent is not None:
                tag.unwrap()


def limpiar_atributos_html(soup):
    """
    Elimina todos los atributos salvo 'id' y 'class'.
    Las clases se normalizan después con normalizar_clases().
    """
    for tag in soup.find_all(True):
        atributos_a_borrar = [attr for attr in tag.attrs if attr not in ('id', 'class')]
        for attr in atributos_a_borrar:
            del tag[attr]


def normalizar_clases(soup):
    """
    Convierte el atributo 'class' (lista) en 'data-clases' con formato '.c1.c2'.
    Elimina el atributo 'class' original para que no interfiera en comparaciones
    de firma estructural ni en la salida HTML final.
    """
    for tag in soup.find_all(True):
        clases = tag.get('class')
        if clases:
            tag['data-clases'] = '.' + '.'.join(clases)
            del tag['class']


def estructura_elemento(tag):
    """
    Devuelve la firma estructural recursiva de un elemento como tupla anidada,
    basada exclusivamente en nombres de etiqueta (sin atributos ni texto).
    Se usa para detectar hermanos estructuralmente idénticos.
    Los placeholders se ignoran en la firma.
    """
    if not hasattr(tag, 'name') or tag.name is None:
        return None
    hijos = tuple(
        estructura_elemento(c)
        for c in tag.children
        if hasattr(c, 'name') and c.name is not None and not c.get('data-placeholder')
    )
    return (tag.name, hijos)


def colapsar_repetidos(soup, max_repeticiones=MAX_REPETICIONES):
    """
    Para cada nodo padre, agrupa sus hijos consecutivos por firma estructural.
    Si un grupo supera max_repeticiones elementos, elimina los sobrantes y
    coloca un marcador visual indicando cuántos han sido omitidos.
    """
    for parent in soup.find_all(True):
        hijos = [
            c for c in parent.children
            if hasattr(c, 'name') and c.name is not None and not c.get('data-placeholder')
        ]

        i = 0
        while i < len(hijos):
            firma = estructura_elemento(hijos[i])

            j = i + 1
            while (
                j < len(hijos)
                and not hijos[j].get('data-placeholder')
                and estructura_elemento(hijos[j]) == firma
            ):
                j += 1

            repeticiones = j - i
            if repeticiones > max_repeticiones:
                excedente = repeticiones - max_repeticiones

                for elem in hijos[i + max_repeticiones:j]:
                    elem.decompose()

                ultimo_conservado = hijos[i + max_repeticiones - 1]
                placeholder = soup.new_tag('div')
                placeholder['data-placeholder'] = str(excedente)
                ultimo_conservado.insert_after(placeholder)

                hijos = [
                    c for c in parent.children
                    if hasattr(c, 'name') and c.name is not None
                ]
                i = i + max_repeticiones + 1
            else:
                i = j


def aplicar_formato_cajas(soup):
    """
    Convierte cada etiqueta de bloque en un <div> con atributo data-etiqueta cuyo
    valor combina:  nombre_etiqueta [#id] [.clase1.clase2]
    Los marcadores de colapso (data-placeholder) se omiten para no sobreescribir
    su estilo propio.
    """
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

        for text_node in tag.find_all(string=True, recursive=False):
            if text_node.strip():
                text_node.extract()


# ---------------------------------------------------------------------------
# Helpers de URL
# ---------------------------------------------------------------------------

def construir_url(ruta_relativa, params=''):
    """
    Devuelve la URL completa para el servidor HTTP local, añadiendo opcionalmente
    un sufijo de query string (p.ej. '?id=neurologia').
    """
    ruta_url = urllib.parse.quote(ruta_relativa.replace('\\', '/'))
    return f"http://localhost:{PUERTO}/{ruta_url}{params}"


def params_para(archivo):
    """
    Devuelve el parámetro de URL que debe usarse al servir 'archivo', o cadena
    vacía si no se requiere ninguno. Solo se aplica a archivos en DIR_P3.
    """
    return PARAMS_URL_DETALLE.get(archivo, '')


# ---------------------------------------------------------------------------
# Captura de pantalla
# ---------------------------------------------------------------------------

def capturar_pantalla(page, ruta_relativa, ruta_salida,
                       viewport=None, full_page=True, ajustar_body=False,
                       params=''):
    page.set_viewport_size(viewport if viewport else {"width": 1280, "height": 800})
    url = construir_url(ruta_relativa, params)
    # networkidle garantiza que finalicen las peticiones fetch de JSON/XML
    page.goto(url, wait_until='networkidle')

    if ajustar_body:
        page.locator("body").screenshot(path=ruta_salida)
    else:
        page.screenshot(path=ruta_salida, full_page=full_page)


def obtener_html_renderizado(page, directorio, archivo):
    """
    Navega a la página vía servidor HTTP (con parámetro de URL si procede) y
    devuelve el HTML completamente renderizado por el motor JS.
    """
    ruta_relativa = os.path.join(directorio, archivo)
    url = construir_url(ruta_relativa, params_para(archivo))
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(url, wait_until='networkidle')
    return page.content()


# ---------------------------------------------------------------------------
# Generación de mapas de etiquetas
# ---------------------------------------------------------------------------

def generar_mapas(archivo, page, directorio, sufijo_salida=''):
    """
    Pipeline completo para un archivo HTML:
      1. Obtener DOM renderizado (JS ejecutado, contenido dinámico incluido)
      2. Eliminar etiquetas no estructurales e inline
      3. Limpiar atributos, conservando id y class
      4. Normalizar clases a data-clases (.c1.c2)
      5. Colapsar hermanos repetidos (> MAX_REPETICIONES copias idénticas)
      6. Aplicar formato de cajas con etiqueta compuesta
      7. Renderizar y capturar con Playwright

    Para páginas de detalle (servicio-especifico, consejo-especifico) se navega
    con el parámetro ?id=... definido en PARAMS_URL_DETALLE, de forma que el
    contenido dinámico sea visible tanto en el mapa como en las capturas.

    Nomenclatura de salida:
      antiguo → {nombre}-boxmodel.png
      actual  → {nombre}-boxmodel-new.png
    """
    nombre_base = archivo.replace('.html', '')

    html_renderizado = obtener_html_renderizado(page, directorio, archivo)
    soup = BeautifulSoup(html_renderizado, 'html.parser')

    limpiar_y_preparar_arbol(soup)
    limpiar_atributos_html(soup)
    normalizar_clases(soup)
    colapsar_repetidos(soup)
    aplicar_formato_cajas(soup)

    estilo_tag = soup.new_tag('style')
    estilo_tag.string = ESTILOS_BOXMODEL
    if not soup.head:
        soup.insert(0, soup.new_tag('head'))
    soup.head.append(estilo_tag)

    ruta_tmp = os.path.join(DIR_OUT_MAPAS, f"{nombre_base}_tmp.html")
    with open(ruta_tmp, 'w', encoding='utf-8') as f:
        f.write(str(soup))

    nombre_salida = f"{nombre_base}-boxmodel{sufijo_salida}.png"
    capturar_pantalla(page, ruta_tmp,
                      os.path.join(DIR_OUT_MAPAS, nombre_salida),
                      ajustar_body=True)
    os.remove(ruta_tmp)


# ---------------------------------------------------------------------------
# Capturas responsivas (solo archivos actuales de petcare-frontend)
# ---------------------------------------------------------------------------

def generar_capturas_reales_responsivas(archivo, page, directorio):
    """
    Genera capturas a tres viewports estándar para los archivos de DIR_P3.
    Si el archivo requiere un parámetro de URL (páginas de detalle), se incluye
    en la navegación para que el contenido sea visible.
    full_page=False garantiza que la imagen tenga exactamente las dimensiones
    del viewport simulado, evitando capturas desproporcionadas.
    """
    nombre_base = archivo.replace('.html', '')
    ruta_relativa = os.path.join(directorio, archivo)
    params = params_para(archivo)

    dispositivos = {
        'desktop': {'width': 1440, 'height': 900},
        'tablet':  {'width': 768,  'height': 1024},
        'mobile':  {'width': 390,  'height': 844},
    }

    for disp, viewport in dispositivos.items():
        ruta_salida = os.path.join(DIR_OUT_CAPTURAS, f"{nombre_base}-{disp}.png")
        capturar_pantalla(page, ruta_relativa, ruta_salida,
                          viewport=viewport, ajustar_body=False,
                          full_page=False, params=params)


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    os.makedirs(DIR_OUT_MAPAS, exist_ok=True)
    os.makedirs(DIR_OUT_CAPTURAS, exist_ok=True)

    print(f"Iniciando servidor local en el puerto {PUERTO}...")
    httpd = ServidorTCPReutilizable(("", PUERTO), ManejadorSilencioso)
    hilo_servidor = threading.Thread(target=httpd.serve_forever, daemon=True)
    hilo_servidor.start()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1. Mapas "antiguos" (other/input) — sin capturas responsivas
        archivos_antiguos = sorted(f for f in os.listdir(DIR_P2) if f.endswith('.html'))
        for archivo in archivos_antiguos:
            print(f"[antiguo] {archivo}...")
            generar_mapas(archivo, page, DIR_P2, sufijo_salida='')

        # 2. Mapas "actuales" + capturas responsivas (petcare-frontend)
        archivos_nuevos = sorted(f for f in os.listdir(DIR_P3) if f.endswith('.html'))
        for archivo in archivos_nuevos:
            print(f"[actual]  {archivo}...")
            generar_mapas(archivo, page, DIR_P3, sufijo_salida='-new')
            generar_capturas_reales_responsivas(archivo, page, DIR_P3)

        browser.close()

    httpd.shutdown()
    httpd.server_close()
    print("\n¡Proceso completado con éxito! Revisa la carpeta doc/")
