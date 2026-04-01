document.addEventListener("DOMContentLoaded", function () {
  $.getJSON("assets/json/clinicas.json", (datos) => {
    const clinicas = datos.clinicas;
    const contenedor = $(".contenedor-tarjetas");
    const template = document.getElementsByTagName("template")[0];
    const estadoVacio = document.getElementById("sin-clinicas-disponibles");

    const convertirHoraAMinutos = (hora) => {
      const [horas, minutos] = hora.split(":").map(Number);
      return (horas * 60) + minutos;
    };

    const estaDisponibleAhora = (horario, minutosActuales) => {
      const partes = horario.split("-");
      if (partes.length !== 2) return false;

      const inicio = convertirHoraAMinutos(partes[0]);
      const fin = convertirHoraAMinutos(partes[1]);

      if (inicio <= fin) {
        return minutosActuales >= inicio && minutosActuales <= fin;
      }

      return minutosActuales >= inicio || minutosActuales <= fin;
    };

    const ahora = new Date();
    const minutosActuales = (ahora.getHours() * 60) + ahora.getMinutes();

    const clinicasDisponibles = clinicas.filter((clinica) => {
      return clinica.urgencias && estaDisponibleAhora(clinica.horario, minutosActuales);
    });

    clinicasDisponibles.forEach((clinica) => {
      const copia = template.content.cloneNode(true);
      copia.querySelector(".foto-clinica").src = clinica.foto;
      copia.querySelector(".titulo-clinica").textContent = clinica.nombre;
      copia.querySelector(".texto-ubicacion").textContent = clinica.ubicacion;
      copia.querySelector(".texto-horario").textContent = clinica.horario;
      copia.querySelector(".texto-telefono").textContent = clinica.telefono;
      copia.querySelector(".llamar-ahora").href = "tel:" + clinica.telefono;
      contenedor.append(copia);
    });

    if (estadoVacio) {
      estadoVacio.hidden = clinicasDisponibles.length > 0;
    }
  });
});
