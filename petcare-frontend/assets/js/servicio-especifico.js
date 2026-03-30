document.addEventListener("DOMContentLoaded", () => {
    cargarServicioEspecifico();
});

async function cargarServicioEspecifico() {
    try {
        const parametros = new URLSearchParams(window.location.search);
        const idServicio = parametros.get("id");

        if (!idServicio) {
            throw new Error("No se indicó el id del servicio");
        }

        const respuesta = await fetch("assets/xml/servicios.xml");

        if (!respuesta.ok) {
            throw new Error("No se pudo cargar el archivo XML");
        }

        const textoXML = await respuesta.text();
        const parser = new DOMParser();
        const xml = parser.parseFromString(textoXML, "application/xml");

        const errorXML = xml.querySelector("parsererror");
        if (errorXML) {
            throw new Error("El XML tiene errores de sintaxis");
        }

        const servicio = xml.querySelector(`servicio[id="${idServicio}"]`);

        if (!servicio) {
            throw new Error("Servicio no encontrado en el XML");
        }

        const nombre = servicio.querySelector("nombre")?.textContent.trim() ?? "";
        const subtitulo = servicio.querySelector("subtitulo")?.textContent.trim() ?? "";
        const banner = servicio.querySelector("banner")?.textContent.trim() ?? "";

        document.getElementById("titulo-servicio").textContent = nombre;
        document.getElementById("subtitulo-servicio").textContent = subtitulo;

        const img = document.getElementById("imagen-servicio");
        img.src = banner;
        img.alt = nombre;

        const contenedorBloques = document.getElementById("bloques-servicio");
        contenedorBloques.innerHTML = "";

        const bloques = servicio.querySelectorAll("bloque");

        bloques.forEach(bloque => {
            const titulo = bloque.querySelector("titulo")?.textContent.trim() ?? "";
            const textos = bloque.querySelectorAll("texto");

            const article = document.createElement("article");

            let html = `<h3>${titulo}</h3>`;
            textos.forEach(texto => {
                html += `<p>${texto.textContent.trim()}</p>`;
            });

            article.innerHTML = html;
            contenedorBloques.appendChild(article);
        });

    } catch (error) {
        console.error("Error al cargar el servicio:", error);

        const contenedorBloques = document.getElementById("bloques-servicio");
        if (contenedorBloques) {
            contenedorBloques.innerHTML = "<p>Error al cargar la información del servicio.</p>";
        }
    }
}