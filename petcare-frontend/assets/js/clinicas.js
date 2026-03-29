
document.addEventListener("DOMContentLoaded", function() {
  $.getJSON("/petcare-frontend/assets/json/clinicas.json", (datos) => {
    let clinicas = datos.clinicas;
    let contenedor = $(".contenedor-tarjetas");
    let template = document.getElementsByTagName("template")[0];

    clinicas.forEach(clinica =>{
      let copia = template.content.cloneNode(true);
      copia.querySelector('.foto-clinica').src=clinica.foto;
      copia.querySelector('.titulo-clinica').textContent=clinica.nombre;
      copia.querySelector('.texto-ubicacion').textContent=clinica.ubicacion;
      copia.querySelector('.texto-horario').textContent=clinica.horario;
      copia.querySelector('.texto-telefono').textContent=clinica.telefono;

      let btncita = copia.querySelector(".pedir-cita");
      btncita.addEventListener("click", () => {
        sessionStorage.setItem('nombreclinica', clinica.nombre);
        sessionStorage.setItem('ubicacionclinica', clinica.ubicacion);
      });
      contenedor.append(copia);
    });

    inicializarBuscador();
    inicializarOrden();
    inicializarHorario();
  });
});

function inicializarBuscador() {
  let formbusqueda=$('form[name="buscarClinica"]');
  let tarjetasclinica=$('.contenedor-tarjetas li');
  let funcbusqueda = (e) => {
    e.preventDefault();
    mostrarTodasLasClinicas();
    let input = $('.input-busqueda');
    let txt = input.val().toLowerCase().trim();
    tarjetasclinica.each(function() {
      let li = $(this);
      let nombreelemento = li.find('.titulo-clinica');
      if (nombreelemento.length > 0) {
        let nombre = nombreelemento.text().toLowerCase();
        if (nombre.includes(txt)) {
          li.css('display', "");
        } else {
          li.css('display', "none");
        }}}
      );
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
    mostrarTodasLasClinicas();
    vaciarInput();

    let tarjetasarray = Array.from(contenedortarjetas.querySelectorAll('li'));
    tarjetasarray.sort(function(a,b){
      let nombrea = a.querySelector('.titulo-clinica').textContent.trim().toLowerCase();
      let nombreb = b.querySelector('.titulo-clinica').textContent.trim().toLowerCase();
      if (ordenascendente){
        if (nombrea < nombreb) return -1;
        if (nombrea > nombreb) return 1;
        return 0;
      }
      else {
        if (nombrea < nombreb) return 1;
        if (nombrea > nombreb) return -1;
        return 0;
      }
    });

    ordenascendente = !ordenascendente;
    horariosencencido = false;
    inicializarHorario();

    tarjetasarray.forEach(function(tarjeta){
      contenedortarjetas.appendChild(tarjeta);
    });
  });
}

function inicializarHorario(){
  let horariosencencido = false;
  let btn = document.querySelectorAll('.contenedor-filtros li button')[1];

  btn.addEventListener("click", (e)=>{
    e.preventDefault();
    horariosencencido = !horariosencencido;
    mostrarTodasLasClinicas();
    vaciarInput();

    let fechahoy = new Date();
    let hora = fechahoy.getHours().toString().padStart(2, '0');
    let minutos = fechahoy.getMinutes().toString().padStart(2, '0');
    let horahoytexto = hora + ":" + minutos;

    let tarjetas = $('.contenedor-tarjetas li');
    tarjetas.each(function(){
      let li = $(this);
      let textohorario = li.find('.texto-horario').text().trim();
      if (horariosencencido) {
        let partes = textohorario.split("-");
        let abre = partes[0].trim();
        let cierra = partes[1].trim();
        if (horahoytexto >= abre && horahoytexto <= cierra) li.css('display', "");
        else li.css("display", "none");
      }
    });
  });
}

function mostrarTodasLasClinicas(){
  $('.contenedor-tarjetas li').each(function(){ $(this).css('display', "")});
}

function vaciarInput(){
  $('.input-busqueda').val("");
}