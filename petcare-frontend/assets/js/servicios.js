let serviciosGlobal = [];
let terminoBusquedaServicios = "";

document.addEventListener("DOMContentLoaded", () => {
    cargarServicios();
    inicializarEventosBusqueda();
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
        
        servicios.forEach(servicio => {
            const id = servicio.getAttribute("id");
            const nombre = servicio.querySelector("nombre")?.textContent.trim() ?? "";
            const imagen = servicio.querySelector("imagen")?.textContent.trim() ?? "";
            const descripcion = servicio.querySelector("descripcion-corta")?.textContent.trim() ?? "";

            serviciosGlobal.push({
                id,
                nombre,
                imagen,
                descripcion
            });
        });

        renderizarServicios();

    } catch (error) {
        console.error("Error al cargar servicios:", error);
        mostrarErrorServicios("Error al cargar los servicios");
    }
}

function inicializarEventosBusqueda() {
    const formularioBusqueda = document.querySelector("#form-busqueda-servicios");
    if (formularioBusqueda) {
        const inputBusqueda = formularioBusqueda.querySelector('input[type="search"]');
        
        // Buscar al enviar el formulario
        formularioBusqueda.addEventListener("submit", (e) => {
            e.preventDefault();
            terminoBusquedaServicios = inputBusqueda.value.trim().toLowerCase();
            renderizarServicios();
        });

        // Buscar al escribir en tiempo real
        inputBusqueda.addEventListener("input", (e) => {
            terminoBusquedaServicios = e.target.value.trim().toLowerCase();
            renderizarServicios();
        });
    }
}

function filtrarServicios() {
    return serviciosGlobal.filter(servicio => {
        return terminoBusquedaServicios === "" ||
            servicio.nombre.toLowerCase().includes(terminoBusquedaServicios) ||
            servicio.descripcion.toLowerCase().includes(terminoBusquedaServicios);
    });
}

function renderizarServicios() {
    const serviciosFiltrados = filtrarServicios();
    const lista = document.getElementById("lista-servicios");

    if (!lista) {
        console.error("No se encontró el contenedor de servicios");
        return;
    }

    lista.innerHTML = "";

    if (serviciosFiltrados.length === 0) {
        lista.innerHTML = '<li style="grid-column: 1 / -1; text-align: center; color: #999; padding: 40px 20px;"><p>No hay servicios que coincidan con tu búsqueda</p></li>';
        return;
    }

    serviciosFiltrados.forEach(servicio => {
        const li = document.createElement("li");

        li.innerHTML = `
            <a class="tarjeta-servicio borde-asimetrico-2" href="servicio-especifico.html?id=${servicio.id}">
                <img src="${servicio.imagen}" class="borde-asimetrico-2" alt="${servicio.nombre}">
                <h3 class="titulo-tarjeta">${servicio.nombre}</h3>
                <p>${servicio.descripcion}</p>
            </a>
        `;

        lista.appendChild(li);
    });
}

function mostrarErrorServicios(mensaje) {
    const lista = document.getElementById("lista-servicios");
    if (lista) {
        lista.innerHTML = `<li style="grid-column: 1 / -1; text-align: center; color: #d32f2f; padding: 40px 20px;"><p>${mensaje}</p></li>`;
    }
}