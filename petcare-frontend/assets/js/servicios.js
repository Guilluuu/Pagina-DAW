let serviciosGlobal = [];
let terminoBusquedaServicios = "";
let estaOrdenado = false;

document.addEventListener("DOMContentLoaded", () => {
    cargarServicios();
    inicializarEventosBusqueda();
    inicializarBotordenamiento();
});

function cargarServicios() {
    // XMLHttpRequest (Objeto integrado en JS para realizar peticiones HTTP)
    let xhr = new XMLHttpRequest();
    
    // Configuración de la petición: Método GET, ruta relativa, petición asíncrona (true)
    xhr.open("GET", "assets/xml/servicios.xml", true);
    
    xhr.onreadystatechange = function () {
        // readyState 4 (operación completada) y status 200 (respuesta HTTP OK)
        if (xhr.readyState === 4 && xhr.status === 200) {
            // responseXML (propiedad que devuelve la respuesta parseada directamente como un árbol de nodos XML)
            let documentoXML = xhr.responseXML;
            procesarServicios(documentoXML);
        }
    };
    
    xhr.onerror = function() {
        console.error("Error al cargar servicios:", xhr.statusText);
        mostrarErrorServicios("Error al cargar los servicios");
    };
    
    xhr.send();
}

function procesarServicios(xmlDoc) {
    try {
        // Extracción de la colección de nodos <servicio> del XML
        let listaServicios = xmlDoc.getElementsByTagName("servicio");

        Array.from(listaServicios).forEach(servicio => {
            // Acceso a los valores internos del XML
            let id = servicio.getAttribute("id");
            let nombre = servicio.getElementsByTagName("nombre")[0].textContent.trim();
            let imagen = servicio.getElementsByTagName("imagen")[0].textContent.trim();
            let descripcion = servicio.getElementsByTagName("descripcion-corta")[0].textContent.trim();

            serviciosGlobal.push({
                id,
                nombre,
                imagen,
                descripcion
            });
        });

        renderizarServicios();

    } catch (error) {
        console.error("Error al procesar servicios:", error);
        mostrarErrorServicios("Error al procesar los servicios");
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

function inicializarBotordenamiento() {
    const btnOrdenar = document.getElementById("btn-ordenar");
    if (btnOrdenar) {
        btnOrdenar.addEventListener("click", () => {
            estaOrdenado = !estaOrdenado;
            btnOrdenar.textContent = estaOrdenado ? "↕ Ordenar Z-A" : "↕ Ordenar A-Z";
            renderizarServicios();
        });
    }
}

function filtrarServicios() {
    let serviciosFiltrados = serviciosGlobal.filter(servicio => {
        return terminoBusquedaServicios === "" ||
            servicio.nombre.toLowerCase().includes(terminoBusquedaServicios) ||
            servicio.descripcion.toLowerCase().includes(terminoBusquedaServicios);
    });

    if (estaOrdenado) {
        serviciosFiltrados.sort((a, b) => {
            return a.nombre.localeCompare(b.nombre, 'es');
        });
    }

    return serviciosFiltrados;
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