document.addEventListener("DOMContentLoaded", () => {
    cargarServicios();
});

async function cargarServicios() {
    try {
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

        const servicios = xml.querySelectorAll("servicio");
        const lista = document.getElementById("lista-servicios");

        lista.innerHTML = "";

        servicios.forEach(servicio => {
            const id = servicio.getAttribute("id");
            const nombre = servicio.querySelector("nombre")?.textContent.trim() ?? "";
            const imagen = servicio.querySelector("imagen")?.textContent.trim() ?? "";
            const descripcion = servicio.querySelector("descripcion-corta")?.textContent.trim() ?? "";

            const li = document.createElement("li");

            li.innerHTML = `
                <a class="tarjeta-servicio" href="servicio-especifico.html?id=${id}">
                    <img src="${imagen}" alt="${nombre}">
                    <h3 class="titulo-tarjeta">${nombre}</h3>
                    <p>${descripcion}</p>
                </a>
            `;

            lista.appendChild(li);
        });

    } catch (error) {
        console.error("Error al cargar servicios:", error);

        const lista = document.getElementById("lista-servicios");
        if (lista) {
            lista.innerHTML = "<li>Error al cargar los servicios.</li>";
        }
    }
}