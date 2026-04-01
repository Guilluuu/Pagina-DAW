let clinicasGlobal = [];

document.addEventListener("DOMContentLoaded", function() {
  $.getJSON("assets/json/clinicas.json", (datos) => {
    clinicasGlobal = datos.clinicas;
    renderizarTarjetas(clinicasGlobal);

    inicializarBuscador();
    inicializarOrden();
    inicializarHorario();

  });
});

function renderizarTarjetas(listaClinicas) {
  let contenedor = $(".contenedor-tarjetas");
  contenedor.empty(); // Método de jQuery que elimina todos los nodos hijos y sus eventos asociados
  let template = document.getElementsByTagName("template")[0];

  listaClinicas.forEach(clinica => {
    let copia = template.content.cloneNode(true);
    copia.querySelector('.foto-clinica').src = clinica.foto;
    copia.querySelector('.titulo-clinica').textContent = clinica.nombre;
    copia.querySelector('.texto-ubicacion').textContent = clinica.ubicacion;
    copia.querySelector('.texto-horario').textContent = clinica.horario;
    copia.querySelector('.texto-telefono').textContent = clinica.telefono;

    let btncita = copia.querySelector(".pedir-cita");
    btncita.addEventListener("click", () => {
      console.log(clinica.nombre);
      console.log(clinica.ubicacion);
      sessionStorage.setItem('nombreclinica', clinica.nombre);
      sessionStorage.setItem('ubicacionclinica', clinica.ubicacion);
    });
    
    contenedor.append(copia);
  });
}


function inicializarBuscador() {
  let formbusqueda = $('form[name="buscarClinica"]');
  let funcbusqueda = (e) => {
    e.preventDefault();
    let txt = $('.input-busqueda').val().toLowerCase().trim();
    
    let clinicasFiltradas = clinicasGlobal.filter(clinica => 
        clinica.nombre.toLowerCase().includes(txt)
    );
    
    renderizarTarjetas(clinicasFiltradas);
  };
  formbusqueda.on('submit', funcbusqueda);
  formbusqueda.on('input', funcbusqueda);
}

function inicializarOrden(){
  let ordenascendente = true;
  let btnordenar = document.querySelector('.contenedor-filtros li:first-child button');
  let contenedortarjetas = document.querySelector('.contenedor-tarjetas');

  btnordenar.addEventListener("click", (e) => {
    e.preventDefault();
    vaciarInput();

    clinicasGlobal.sort(function(a, b){
      let nombrea = a.nombre.toLowerCase();
      let nombreb = b.nombre.toLowerCase();
      if (ordenascendente){
        if (nombrea < nombreb) return -1;
        if (nombrea > nombreb) return 1;
        return 0;
      } else {
        if (nombrea < nombreb) return 1;
        if (nombrea > nombreb) return -1;
        return 0;
      }
    });

    ordenascendente = !ordenascendente;
    // inicializarHorario();

    renderizarTarjetas(clinicasGlobal);
  });
}

function inicializarHorario() {
  let horariosencendido = false;
  let btn = document.querySelectorAll('.contenedor-filtros li button')[1];

  btn.addEventListener("click", (e) => {
    e.preventDefault();
    horariosencendido = !horariosencendido;
    vaciarInput();

    if (horariosencendido) {
      let fechahoy = new Date();
      let hora = fechahoy.getHours().toString().padStart(2, '0');
      let minutos = fechahoy.getMinutes().toString().padStart(2, '0');
      let horahoytexto = hora + ":" + minutos;

      let clinicasFiltradas = clinicasGlobal.filter(clinica => {
        let partes = clinica.horario.split("-");
        let abre = partes[0].trim();
        let cierra = partes[1].trim();
        return horahoytexto >= abre && horahoytexto <= cierra;
      });
      renderizarTarjetas(clinicasFiltradas);
    } else {
      renderizarTarjetas(clinicasGlobal);
    }
  });
}

function vaciarInput(){
  $('.input-busqueda').val("");
}