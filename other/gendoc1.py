import os
import urllib.parse
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# Configuración de directorios
DIR_P3 = 'petcare-frontend'
DIR_P2 = 'petcare-frontend-p2' # Carpeta con los HTML de la Práctica 2 (para comparar)

DIR_OUT_MAPAS = 'doc/mapasDeEtiquetas'
DIR_OUT_CAMBIOS = 'doc/mapasDeEtiquetas-cambios'
DIR_OUT_CAPTURAS = 'doc/capturas_responsivas'

# Etiquetas estrictamente de bloque o contenedor (se desenvolverán (unwrap) las inline como <a>, <span>, <strong>...)
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
    body { font-family: monospace; background: #f4f4f4; padding: 20px; }
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
    /* Estilos para resaltar cambios */
    *[data-cambio="nuevo"] { border-color: #27ae60 !important; border-width: 3px !important; }
    *[data-cambio="nuevo"]::before { background: #27ae60 !important; content: attr(data-etiqueta) " (NUEVO)" !important; }
    *[data-cambio="atributos"] { border-color: #d35400 !important; border-style: dashed !important; border-width: 3px !important;}
    *[data-cambio="atributos"]::before { background: #d35400 !important; content: attr(data-etiqueta) " (ATRIBUTOS MODIFICADOS)" !important; }
"""

def limpiar_y_preparar_arbol(soup):
    """Elimina etiquetas innecesarias y desenvuelve (unwrap) las inline, dejando solo la estructura de bloques"""
    # Usamos una lista para no alterar el iterador mientras modificamos el DOM
    for tag in list(soup.find_all(True)):
        if tag.name in ETIQUETAS_ELIMINAR:
            tag.decompose()
        elif tag.name not in ETIQUETAS_BLOQUE:
            tag.unwrap() # Elimina la etiqueta pero conserva su contenido interno

def aplicar_formato_cajas(soup):
    """Convierte las etiquetas restantes en divs con el atributo data-etiqueta"""
    for tag in soup.find_all(True):
        if tag.name == 'html' or tag.name == 'body':
            continue
        tag['data-etiqueta'] = tag.name
        tag.name = 'div'
        # Vaciamos el texto suelto para que el diagrama sea limpio
        for text_node in tag.find_all(string=True, recursive=False):
            if text_node.strip():
                text_node.extract()

def comparar_arboles(nodo_p2, nodo_p3):
    """Compara recursivamente dos árboles DOM para detectar etiquetas nuevas o atributos modificados"""
    if not hasattr(nodo_p3, 'name') or nodo_p3.name is None:
        return

    # Si no existe en P2, es completamente nuevo
    if nodo_p2 is None:
        nodo_p3['data-cambio'] = 'nuevo'
        for child in nodo_p3.find_all(True):
            child['data-cambio'] = 'nuevo'
        return

    # Comparar atributos (ignorando los propios del script)
    attrs_p2 = {k: v for k, v in nodo_p2.attrs.items() if k not in ['data-etiqueta', 'data-cambio']}
    attrs_p3 = {k: v for k, v in nodo_p3.attrs.items() if k not in ['data-etiqueta', 'data-cambio']}
    
    if attrs_p2 != attrs_p3:
        nodo_p3['data-cambio'] = 'atributos'

    # Comparación recursiva de hijos
    hijos_p2 = [c for c in nodo_p2.children if c.name is not None]
    hijos_p3 = [c for c in nodo_p3.children if c.name is not None]

    for i, hijo_p3 in enumerate(hijos_p3):
        hijo_p2 = hijos_p2[i] if i < len(hijos_p2) else None
        # Si las etiquetas no coinciden, asumimos que se insertó algo nuevo
        if hijo_p2 and hijo_p2.name != hijo_p3.name:
            hijo_p2 = None 
        comparar_arboles(hijo_p2, hijo_p3)

def capturar_pantalla(page, ruta_html, ruta_salida, viewport=None, full_page=True):
    """Toma una captura de pantalla usando Playwright"""
    if viewport:
        page.set_viewport_size(viewport)
    
    # URL absoluta local
    url_local = "file://" + urllib.parse.quote(os.path.abspath(ruta_html).replace('\\', '/'))
    page.goto(url_local, wait_until='networkidle')
    page.screenshot(path=ruta_salida, full_page=full_page)

def generar_mapas(archivo, page):
    nombre_base = archivo.replace('.html', '')
    ruta_p3 = os.path.join(DIR_P3, archivo)
    ruta_p2 = os.path.join(DIR_P2, archivo)

    with open(ruta_p3, 'r', encoding='utf-8') as f:
        soup_p3 = BeautifulSoup(f, 'html.parser')

    # Limpieza estructural (solo dejamos bloques)
    limpiar_y_preparar_arbol(soup_p3)

    # 1. GENERAR MAPA NORMAL
    soup_normal = BeautifulSoup(str(soup_p3), 'html.parser')
    aplicar_formato_cajas(soup_normal)
    
    estilo_tag = soup_normal.new_tag('style')
    estilo_tag.string = ESTILOS_BOXMODEL
    if not soup_normal.head:
        soup_normal.insert(0, soup_normal.new_tag('head'))
    soup_normal.head.append(estilo_tag)

    ruta_tmp_normal = os.path.join(DIR_OUT_MAPAS, f"{nombre_base}_tmp.html")
    with open(ruta_tmp_normal, 'w', encoding='utf-8') as f:
        f.write(str(soup_normal))
    
    capturar_pantalla(page, ruta_tmp_normal, os.path.join(DIR_OUT_MAPAS, f"{nombre_base}-etiquetas.png"))
    os.remove(ruta_tmp_normal) # Limpiamos el temporal

    # 2. GENERAR MAPA DE CAMBIOS (si existe versión P2)
    if os.path.exists(ruta_p2):
        with open(ruta_p2, 'r', encoding='utf-8') as f:
            soup_p2 = BeautifulSoup(f, 'html.parser')
        
        limpiar_y_preparar_arbol(soup_p2)
        
        # Comparamos la estructura limpia P3 con la limpia P2
        comparar_arboles(soup_p2.body, soup_p3.body)
        
        # Aplicamos el formato caja y estilos
        aplicar_formato_cajas(soup_p3)
        estilo_tag_cambios = soup_p3.new_tag('style')
        estilo_tag_cambios.string = ESTILOS_BOXMODEL
        if not soup_p3.head:
            soup_p3.insert(0, soup_p3.new_tag('head'))
        soup_p3.head.append(estilo_tag_cambios)

        ruta_tmp_cambios = os.path.join(DIR_OUT_CAMBIOS, f"{nombre_base}_cambios_tmp.html")
        with open(ruta_tmp_cambios, 'w', encoding='utf-8') as f:
            f.write(str(soup_p3))
        
        capturar_pantalla(page, ruta_tmp_cambios, os.path.join(DIR_OUT_CAMBIOS, f"{nombre_base}-cambios.png"))
        os.remove(ruta_tmp_cambios)
    else:
        print(f"  [!] No se encontró {archivo} en {DIR_P2}. Se omite mapa de cambios.")

def generar_capturas_reales_responsivas(archivo, page):
    nombre_base = archivo.replace('.html', '')
    ruta_html = os.path.join(DIR_P3, archivo)

    dispositivos = {
        'desktop': {'width': 1920, 'height': 1080},
        'tablet': {'width': 768, 'height': 1024},
        'mobile': {'width': 375, 'height': 667}
    }

    for disp, viewport in dispositivos.items():
        ruta_salida = os.path.join(DIR_OUT_CAPTURAS, f"{nombre_base}-{disp}.png")
        capturar_pantalla(page, ruta_html, ruta_salida, viewport=viewport)

if __name__ == '__main__':
    # Crear directorios de salida
    os.makedirs(DIR_OUT_MAPAS, exist_ok=True)
    os.makedirs(DIR_OUT_CAMBIOS, exist_ok=True)
    os.makedirs(DIR_OUT_CAPTURAS, exist_ok=True)

    archivos_html = [f for f in os.listdir(DIR_P3) if f.endswith('.html')]

    if not archivos_html:
        print(f"No hay archivos HTML en {DIR_P3}.")
    else:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            for archivo in archivos_html:
                print(f"Procesando {archivo}...")
                
                # 1 y 2: Mapas de etiquetas (Normales y Cambios)
                generar_mapas(archivo, page)

                # 3: Capturas reales de la web (Escritorio, Tablet, Móvil)
                generar_capturas_reales_responsivas(archivo, page)

            browser.close()
        print("\n¡Proceso completado con éxito! Revisa la carpeta doc/")
