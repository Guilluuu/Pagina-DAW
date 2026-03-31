document.addEventListener("DOMContentLoaded", () => {
    cargarConsejos();
    inicializarEventos();
});

let consejosGlobal = [];
let categoriaActual = "perro";
let terminoBusqueda = "";

async function cargarConsejos() {
    try {
        const respuesta = await fetch("assets/json/consejos.json");

        if (!respuesta.ok) {
            throw new Error("No se pudo cargar el archivo JSON");
        }

        const datos = await respuesta.json();
        consejosGlobal = datos.consejos;

        renderizarConsejos();

    } catch (error) {
        console.error("Error al cargar los consejos:", error);
        mostrarError("Error al cargar los consejos");
    }
}

function inicializarEventos() {
    // Eventos de los botones de categoría
    const botonesCategoria = document.querySelectorAll("#categoria-animales .nav-link");
    botonesCategoria.forEach(boton => {
        boton.addEventListener("click", (e) => {
            const target = e.currentTarget.getAttribute("data-bs-target");
            
            if (target === "#perros-tab-pane") {
                categoriaActual = "perro";
            } else if (target === "#gatos-tab-pane") {
                categoriaActual = "gato";
            } else if (target === "#otros-tab-pane") {
                categoriaActual = "otros";
            }

            renderizarConsejos();
        });
    });

    // Evento del formulario de búsqueda
    const formularioBusqueda = document.querySelector('form[name="buscarClinica"]');
    if (formularioBusqueda) {
        const inputBusqueda = formularioBusqueda.querySelector('input[type="search"]');
        const botonBusqueda = formularioBusqueda.querySelector('button[type="submit"]');

        // Buscar al enviar el formulario
        formularioBusqueda.addEventListener("submit", (e) => {
            e.preventDefault();
            terminoBusqueda = inputBusqueda.value.trim().toLowerCase();
            renderizarConsejos();
        });

        // Buscar al escribir en tiempo real
        inputBusqueda.addEventListener("input", (e) => {
            terminoBusqueda = e.target.value.trim().toLowerCase();
            renderizarConsejos();
        });
    }
}

function filtrarConsejos() {
    return consejosGlobal.filter(consejo => {
        const cumpleCategoria = consejo.categoria === categoriaActual;
        
        const cumpleBusqueda = terminoBusqueda === "" || 
            consejo.titulo.toLowerCase().includes(terminoBusqueda) ||
            consejo.preview.toLowerCase().includes(terminoBusqueda) ||
            consejo.etiquetas.some(etiqueta => etiqueta.toLowerCase().includes(terminoBusqueda));

        return cumpleCategoria && cumpleBusqueda;
    });
}

function renderizarConsejos() {
    const consejosFiltr = filtrarConsejos();
    const contenedor = document.querySelector("ul.row.list-unstyled");

    if (!contenedor) {
        console.error("No se encontró el contenedor de consejos");
        return;
    }

    // Limpiar contenedor
    contenedor.innerHTML = "";

    if (consejosFiltr.length === 0) {
        contenedor.innerHTML = '<li class="col-12 text-center text-muted mt-4"><p>No hay consejos que coincidan con tu búsqueda</p></li>';
        return;
    }

    consejosFiltr.forEach(consejo => {
        const card = crearCard(consejo);
        contenedor.appendChild(card);
    });
}

function crearCard(consejo) {
    const li = document.createElement("li");
    li.className = "col-12 col-md-6 p-0 mb-5";

    // Generar badges para cada etiqueta
    const etiquetasHtml = (consejo.etiquetas || [])
        .map(etiqueta => `<span class="card-text badge bg-success bg-opacity-10 text-success fw-normal mb-2 me-2">${etiqueta}</span>`)
        .join("");

    const htmlContenido = `
        <article class="card h-100 border-white borde-asimetrico d-flex flex-column m-4 shadow">
            <img class="card-img-top borde-asimetrico-top-right w-100 imagen-carta" 
                 src="${consejo.imagen}" 
                 alt="${consejo.titulo}">
            <section class="card-body d-flex flex-column">
                <a href="consejo-especifico.html?id=${consejo.id}" 
                   class="h5 fw-bold text-dark text-decoration-none d-block mb-2">
                    ${consejo.titulo}
                </a>
                <div class="mb-2">
                    ${etiquetasHtml}
                </div>
                <p class="card-text mb-0 p-carta" >
                    ${consejo.preview}
                </p>
            </section>
        </article>
    `;

    li.innerHTML = htmlContenido;
    return li;
}

function mostrarError(mensaje) {
    const contenedor = document.querySelector("ul.row.list-unstyled");
    if (contenedor) {
        contenedor.innerHTML = `<li class="col-12 text-center text-danger mt-4"><p>${mensaje}</p></li>`;
    }
}
