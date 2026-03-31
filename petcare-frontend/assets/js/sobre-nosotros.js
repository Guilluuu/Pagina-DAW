document.addEventListener("DOMContentLoaded", () => {
    // Estructura de datos en memoria simulando un origen de datos
const repositorioTextos = {
    sostenibilidad: `
        <p>En PetCare, nuestro principal compromiso se sustenta sobre tres pilares fundamentales: el cuidado de las mascotas, el bienestar de nuestro equipo y la protección del medio ambiente. Creemos que estas conexiones son vitales para garantizar el más alto nivel de calidad médica.</p>
        <p>Trabajamos activamente en la optimización de recursos en todas nuestras clínicas y promovemos un uso antimicrobiano responsable para combatir la resistencia a los antibióticos, una prioridad absoluta en nuestra práctica clínica diaria. Nuestros programas de reciclaje y gestión de residuos biológicos se alinean con los estándares internacionales más rigurosos.</p>
        <p>Además, fomentamos un entorno de trabajo seguro y motivador. La formación continua y el equilibrio personal-profesional de nuestros veterinarios y auxiliares son esenciales para ofrecer siempre la mejor atención posible. Invertimos en bienestar laboral, programas de mentoría y oportunidades de especialización para cada miembro del equipo.</p>
        <p>Nuestro compromiso también incluye iniciativas comunitarias de educación sobre tenencia responsable de mascotas y campañas de esterilización subsidiada para animales en situación vulnerable.</p>
    `,
    
    principios: `
        <p>Como red de clínicas comprometida con el bienestar animal, en PetCare compartimos principios básicos que guían nuestra forma de interactuar:</p>
        <ul>
            <li><strong>Calidad:</strong> Ofrecemos atención de primer nivel, innovando constantemente en diagnósticos y tratamientos. Nuestros equipos incluyen resonancia magnética, tomografía computarizada y laboratorios de análisis de última generación.</li>
            <li><strong>Responsabilidad:</strong> Actuamos con ética y transparencia, asumiendo la salud de tu mascota como nuestra máxima prioridad. Cada decisión clínica se toma pensando únicamente en el bienestar del animal.</li>
            <li><strong>Empatía:</strong> Comprendemos el vínculo entre los animales y sus familias, brindando un trato humano y cercano. Nuestro personal está capacitado en comunicación empática y manejo del estrés tanto en mascotas como en sus dueños.</li>
            <li><strong>Eficiencia:</strong> Utilizamos nuestros recursos tecnológicos y humanos de manera óptima para lograr los mejores resultados sin comprometer la calidad de atención individualizada.</li>
        </ul>
        <p>Estos valores nos unen a lo largo de todas nuestras instalaciones y protocolos de actuación, reflejándose en la satisfacción de más de 50,000 familias anualmente.</p>
    `,
    
    medicina: `
        <p>El propósito de PetCare es mantener la medicina veterinaria en su nivel más elevado. Para ello, apostamos fuertemente por la capacitación de nuestros profesionales y la inversión en equipamiento tecnológico avanzado, desde consultas de prevención hasta áreas de hospitalización y cirugía equipadas con monitoreo continuo.</p>
        <p>Fomentamos el intercambio continuo de conocimientos entre los especialistas de nuestras distintas clínicas. Colaborando codo con codo, logramos resolver los casos más exigentes y garantizamos que tu mascota reciba el diagnóstico más preciso. Participamos activamente en congresos internacionales y publicamos investigaciones en revista especializadas.</p>
        <p>Asimismo, mantenemos protocolos rigurosos de higiene y control de infecciones en todos nuestros quirófanos, asegurando un entorno clínico totalmente seguro. Nuestras instalaciones cumplen certificaciones ISO y realizan auditorías externas trimestrales.</p>
    `,
    
    por_que: `
        <p>Elegir PetCare significa confiar en una red de centros veterinarios rigurosamente preparados. Cada una de nuestras clínicas está equipada para ofrecer una asistencia integral, respaldada por nuestro servicio de Urgencias disponible 24/7 y equipo de especialistas en cirugía, dermatología, cardiología y oncología.</p>
        <p>Nos enorgullece atraer a grandes profesionales del sector, muchos de ellos diplomados por colegios veterinarios internacionales. Esto nos permite abordar desde procedimientos rutinarios hasta intervenciones especializadas con total garantía. Siempre evaluaremos todas las opciones contigo, con total transparencia, antes de iniciar cualquier tratamiento, incluyendo presupuestos detallados y planes de pago flexibles.</p>
        <p>Gracias a la confianza diaria de nuestros clientes, seguimos desarrollando la atención veterinaria del futuro, centrada en el amor por los animales y el rigor médico. Nuestro índice de satisfacción superior al 98% nos motiva a mejorar constantemente.</p>
    `
};

    // const primerBoton = document.querySelector(".btn-pestana:first-of-type");
    
    // // Referencias a los nodos del DOM (Document Object Model - Modelo de Objetos del Documento)
    const botones = document.querySelectorAll(".btn-pestana");
    const contenedorDespliegue = document.getElementById("area-despliegue-texto");
    
    (botones[0]).classList.add("activo");
    contenedorDespliegue.innerHTML = repositorioTextos[(botones[0]).getAttribute("data-clave")];

    // Asignación de manejadores de eventos
    botones.forEach(boton => {
        boton.addEventListener("click", (evento) => {
            // Actualización del estado visual de la interfaz
            botones.forEach(btn => btn.classList.remove("activo"));
            evento.currentTarget.classList.add("activo");

            // Recuperación e inyección del estado de datos
            const claveSeleccionada = evento.currentTarget.getAttribute("data-clave");
            contenedorDespliegue.innerHTML = repositorioTextos[claveSeleccionada];
        });
    });
});