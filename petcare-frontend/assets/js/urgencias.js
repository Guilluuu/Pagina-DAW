document.addEventListener("DOMContentLoaded", function() {
  $.getJSON("assets/json/clinicas.json", (datos) => {
    let clinicas = datos.clinicas;
    let contenedor = $(".contenedor-tarjetas");
    let template = document.getElementsByTagName("template")[0];

    clinicas.forEach(clinica =>{
      let copia = template.content.cloneNode(true);
      if(clinica.urgencias){
        copia.querySelector('.foto-clinica').src=clinica.foto;
        copia.querySelector('.titulo-clinica').textContent=clinica.nombre;
        copia.querySelector('.texto-ubicacion').textContent=clinica.ubicacion;
        copia.querySelector('.texto-horario').textContent=clinica.horario;
        copia.querySelector('.texto-telefono').textContent=clinica.telefono;
        copia.querySelector('.llamar-ahora').href="tel:"+clinica.telefono;
        contenedor.append(copia);
      }
      
    });
  });
});