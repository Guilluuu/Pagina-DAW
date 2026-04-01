/**
 * Actualiza el formulario con los datos de la clínica almacenados en SessionStorage
 */
function actualizarDatosClinica() {
  // 1. Recuperación de la información almacenada en SessionStorage
  let nombreclinica = sessionStorage.getItem('nombreclinica');
  let ubicacionclinica = sessionStorage.getItem('ubicacionclinica');
  
  // 2. Modificación del DOM si existen los datos
  if (nombreclinica) {
    document.querySelector(".titulo").textContent = nombreclinica;
  }
  
  if (ubicacionclinica) {
    document.getElementById('texto-ubicacion-cita').textContent = ubicacionclinica;
  }
}

// Se ejecuta al cargar el iframe
document.addEventListener("DOMContentLoaded", function() {
  actualizarDatosClinica();
});

// Escucha cambios en SessionStorage desde otras ventanas/iframes
window.addEventListener('storage', function(event) {
  if (event.key === 'nombreclinica' || event.key === 'ubicacionclinica' || event.key === null) {
    actualizarDatosClinica();
  }
});