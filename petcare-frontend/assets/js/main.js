document.addEventListener("DOMContentLoaded", function name() {
    document.querySelector('.menu-hamburguesa-moviles').addEventListener('click', function () {
        document.querySelector('.main-navbar').classList.toggle('menu-abierto');
    });

      let formbusqueda = document.querySelector('form[name="buscarClinica"]');
  let tarjetasclinica = document.querySelectorAll('.contenedor-tarjetas li');

  //búsqueda en clínicas
  formbusqueda.addEventListener('submit', function(e){
    e.preventDefault();
    let input = document.querySelector('.input-busqueda');
    let txt = input.value.toLowerCase().trim();
    tarjetasclinica.forEach(function(li){
      let nombreelemento = li.querySelector('.titulo-clinica');
      if (nombreelemento) {
        let nombre = nombreelemento.textContent.toLowerCase();
        if(nombre.includes(txt)) li.style.display="";
        else li.style.display="none";
      }
    });
  });

  //ordenar en clínicas
  let btnordenar = document.querySelector('.contenedor-filtros li:first-child button');
  let contenedortarjetas = document.querySelector('.contenedor-tarjetas');
  let ordenascendente = true;

  btnordenar.addEventListener("click", function(e) {
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


