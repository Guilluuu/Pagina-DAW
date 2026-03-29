document.addEventListener("DOMContentLoaded", function(){
  let nombreclinica = sessionStorage.getItem('nombreclinica');
  let ubicacionclinica = sessionStorage.getItem('ubicacionclinica');
  if (nombreclinica){
    document.querySelector(".titulo").textContent = nombreclinica;
  }
  if (ubicacionclinica){
    document.getElementById('texto-ubicacion-cita').textContent = ubicacionclinica;
  }
});