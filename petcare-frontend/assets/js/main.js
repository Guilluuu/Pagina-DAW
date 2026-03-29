document.addEventListener("DOMContentLoaded", function () {
  let botonHamburguesa = document.querySelector('.menu-hamburguesa-moviles');
  if (botonHamburguesa) {
      botonHamburguesa.addEventListener('click', function () {
        document.querySelector('.main-navbar').classList.toggle('menu-abierto');
      });
    }
});

