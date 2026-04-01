let consejosGlobal = [];
let intervaloConsejos;

document.addEventListener("DOMContentLoaded", () => {
    fetch("assets/json/consejos.json")
        .then(respuesta => respuesta.json())
        .then(datos => {
            consejosGlobal = datos.consejos;
            actualizarConsejosIndex();
            intervaloConsejos = setInterval(actualizarConsejosIndex, 10000);
        })
        .catch(error => console.error("Error al cargar consejos:", error));
    
    inicializarBuscadorClinicas();
});

function inicializarBuscadorClinicas() {
    const formularioBusqueda = document.querySelector(".contenedor-portada-formulario");
    if (formularioBusqueda) {
        formularioBusqueda.addEventListener("submit", (e) => {
            e.preventDefault();
            const inputBusqueda = formularioBusqueda.querySelector('input[type="search"]');
            const termino = inputBusqueda.value.trim();
            
            if (termino) {
                // Redirigir a clinicas.html y establecer el término de búsqueda
                window.location.href = `clinicas.html?clinica=${encodeURIComponent(termino)}`;
            }
        });
    }
}

function actualizarConsejosIndex() {
    if (consejosGlobal.length < 2) return;

    let indice1 = Math.floor(Math.random() * consejosGlobal.length);
    let indice2;
    
    do {
        indice2 = Math.floor(Math.random() * consejosGlobal.length);
    } while (indice1 === indice2);

    let consejo1 = consejosGlobal[indice1];
    let consejo2 = consejosGlobal[indice2];

    renderizarConsejos([consejo1, consejo2]);
}

function renderizarConsejos(listaConsejos) {
    let contenedor = document.getElementById("contenedor-consejos-index");
    
    contenedor.classList.add("fade-out");

    setTimeout(() => {
        contenedor.innerHTML = "";

        listaConsejos.forEach((consejo, indice) => {
            let direccion = indice === 0 ? "tarjeta-servicio-inicio--imagen-izquierda" : "tarjeta-servicio-inicio--imagen-derecha";

            let htmlContenido = `
                <a href="consejo-especifico.html?id=${consejo.id}" class="consejo-home-enlace">
                    <article class="tarjeta-servicio-inicio ${direccion}">
                        <figure class="tarjeta-servicio-inicio-imagen">
                            <img src="${consejo.imagen}" class="borde-asimetrico-2" alt="${consejo.titulo}">
                        </figure>
                        <section class="tarjeta-servicio-inicio-texto">
                            <h3>${consejo.titulo}</h3>
                            <p>${consejo.preview}</p>
                        </section>
                    </article>
                </a>
            `;
            contenedor.innerHTML += htmlContenido;
        });

        contenedor.classList.remove("fade-out");
        contenedor.classList.add("fade-in");

        setTimeout(() => {
            contenedor.classList.remove("fade-in");
        }, 500);
    }, 300);
}