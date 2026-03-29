document.addEventListener("DOMContentLoaded", function name() {

  let formbusqueda=$('form[name="buscarClinica"]');
  let tarjetasclinica=$('.contenedor-tarjetas li');
  //TODO aquí está el jquery
  //búsqueda en clínicas

  let funcbusqueda = (e) => {
    e.preventDefault();
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


  //ordenar en clínicasç
  //TODO aquí es donde está la sintaxis propia de JSE6
  let btnordenar = document.querySelector('.contenedor-filtros li:first-child button');
  let contenedortarjetas = document.querySelector('.contenedor-tarjetas');
  let ordenascendente = true;

  btnordenar.addEventListener("click", (e) => {
    e.preventDefault();

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

    tarjetasarray.forEach(function(tarjeta){
      contenedortarjetas.appendChild(tarjeta);
    });
  });
  
});