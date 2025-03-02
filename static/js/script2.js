document.addEventListener('DOMContentLoaded', () => {
    const comentario = document.getElementById('comentario');
    const archivo = document.getElementById('archivo');
    const fechaInicio = document.getElementById('fechaInicio');
    const fechaFin = document.getElementById('fechaFin');
    const form = document.getElementById("formularioPermiso");
    let diasDisponibles = 0;

    // Función para obtener días disponibles de vacaciones
    async function obtenerDiasVacaciones() {
        try {
            const response = await fetch('/pedirvacaciones');
            const data = await response.json();
            if (data.error) {
                alert(data.error);
            } else {
                diasDisponibles = data.dias_disponibles;
                alert(`Tienes ${diasDisponibles} días de vacaciones disponibles.`);
            }
        } catch (error) {
            console.error('Error al obtener días de vacaciones:', error);
        }
    }

    // Deshabilitar campos para VACACIONES y obtener días disponibles
    document.querySelectorAll('input[name="tipo"]').forEach(radio => {
        radio.addEventListener('change', async (e) => {
            const isVacaciones = e.target.value === 'VACACIONES';
            comentario.disabled = isVacaciones;
            comentario.style.backgroundColor = isVacaciones ? '#f5f5f5' : 'white';
            archivo.disabled = isVacaciones;
            archivo.style.backgroundColor = isVacaciones ? '#f5f5f5' : 'white';
            
            if (isVacaciones) {
                await obtenerDiasVacaciones();
            }
        });
    });

    // Validación en tiempo real de fechas
    fechaInicio.addEventListener('input', validarFechas);
    fechaFin.addEventListener('input', validarFechas);

    function validarFechas() {
        const inicio = new Date(fechaInicio.value);
        const fin = new Date(fechaFin.value);
        if (fechaInicio.value && fechaFin.value && fin < inicio) {
            alert("La fecha de fin no puede ser anterior a la fecha de inicio.");
            fechaFin.value = "";
        }
    }

    // Validación al enviar el formulario
    form.addEventListener("submit", function (event) {
        const tipo = document.querySelector('input[name="tipo"]:checked')?.value;
        const fechaInicioVal = fechaInicio.value;
        const fechaFinVal = fechaFin.value;
        const archivoSubido = archivo.files.length > 0;
        const comentarioTexto = comentario.value.trim();

        if (!fechaInicioVal || !fechaFinVal) {
            alert("Selecciona fechas válidas.");
            event.preventDefault();
            return;
        }

        const inicioDate = new Date(fechaInicioVal);
        const finDate = new Date(fechaFinVal);
        const diasSolicitados = Math.ceil((finDate - inicioDate) / (1000 * 60 * 60 * 24)) + 1;

        if (finDate < inicioDate) {
            alert("La fecha de fin no puede ser anterior a la fecha de inicio.");
            event.preventDefault();
            return;
        }

        if (tipo === "VACACIONES" && diasSolicitados > diasDisponibles) {
            alert(`⚠ Días disponibles: ${diasDisponibles} | Solicitaste: ${diasSolicitados}`);
            event.preventDefault();
            return;
        }        

        if (tipo === "PERMISO" || tipo === "INCAPACIDAD") {
            if (!archivoSubido) {
                alert("Debes subir un archivo justificante.");
                event.preventDefault();
                return;
            }
            if (!comentarioTexto) {
                alert("Debes escribir un comentario.");
                event.preventDefault();
                return;
            }
        }
    });
});

// Funciones de control del modal
function openSolicitudModal() {
    document.getElementById('solicitudModal').style.display = 'block';
}

function closeSolicitudModal() {
    document.getElementById('solicitudModal').style.display = 'none';
}


// Control del dropdown de tipos
document.getElementById('tipoSolicitudBtn').addEventListener('click', function(e) {
    e.stopPropagation();
    document.getElementById('tipoSolicitudMenu').classList.toggle('show');
});

// Cerrar dropdowns y el modal al hacer clic fuera
window.addEventListener('click', function(e) {
    if (!e.target.closest('.dropdown')) {
        document.querySelectorAll('.dropdown-content').forEach(dropdown => {
            dropdown.classList.remove('show');
        });
    }
    const modal = document.getElementById('solicitudModal');
    if (e.target === modal) {
        closeSolicitudModal();
    }
});