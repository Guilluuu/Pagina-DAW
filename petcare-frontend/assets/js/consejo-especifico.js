document.addEventListener("DOMContentLoaded", () => {
    cargarConsejoEspecifico();
});

async function cargarConsejoEspecifico() {
    try {
        const parametros = new URLSearchParams(window.location.search);
        const idConsejo = parametros.get("id");

        if (!idConsejo) {
            throw new Error("No se indicó el id del consejo");
        }

        const respuesta = await fetch("assets/json/consejos.json");

        if (!respuesta.ok) {
            throw new Error("No se pudo cargar el archivo JSON");
        }

        const datos = await respuesta.json();
        const consejo = datos.consejos.find(c => c.id === idConsejo);

        if (!consejo) {
            throw new Error("Consejo no encontrado en el JSON");
        }

        const titulo = consejo.titulo ?? "";
        const preview = consejo.preview ?? "";
        const imagen = consejo.imagen ?? "";
        const contenido = consejo.contenido ?? "";

        document.getElementById("titulo-consejo").textContent = titulo;
        document.getElementById("subtitulo-consejo").textContent = preview;

        const img = document.getElementById("imagen-consejo");
        img.src = imagen;
        img.alt = titulo;

        const contenedorBloques = document.getElementById("bloques-consejo");
        contenedorBloques.innerHTML = "";

        if (contenido) {
            // El contenido viene estructurado con "Conclusión:", "Evidencia de soporte:" y "Matices o limitaciones:"
            const articulos = dividirContenido(contenido);

            articulos.forEach((articulo) => {
                const article = document.createElement("article");
                let html = "";

                // Crear título basado en el patrón encontrado
                if (articulo.titulo) {
                    html += `<h3>${articulo.titulo}</h3>`;
                }

                // Añadir el contenido
                html += `<p>${articulo.contenido}</p>`;

                article.innerHTML = html;
                contenedorBloques.appendChild(article);
            });

            // Si no hay estructura detectada, mostrar todo como un párrafo
            if (articulos.length === 0) {
                const article = document.createElement("article");
                article.innerHTML = `<p>${contenido}</p>`;
                contenedorBloques.appendChild(article);
            }
        }

    } catch (error) {
        console.error("Error al cargar el consejo:", error);

        const contenedorBloques = document.getElementById("bloques-consejo");
        if (contenedorBloques) {
            contenedorBloques.innerHTML = "<p>Error al cargar la información del consejo.</p>";
        }
    }
}

function dividirContenido(contenido) {
    const bloques = [];
    const patrones = [
        { titulo: "Conclusión", regex: /Conclusión:([^]*?)(?=Evidencia de soporte:|Matices o limitaciones:|$)/ },
        { titulo: "Evidencia de soporte", regex: /Evidencia de soporte:([^]*?)(?=Matices o limitaciones:|$)/ },
        { titulo: "Matices o limitaciones", regex: /Matices o limitaciones:([^]*?)$/ }
    ];

    patrones.forEach(seccion => {
        const match = contenido.match(seccion.regex);
        if (match && match[1]) {
            bloques.push({
                titulo: seccion.titulo,
                contenido: match[1].trim()
            });
        }
    });

    return bloques;
}