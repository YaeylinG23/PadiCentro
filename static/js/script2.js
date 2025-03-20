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

    // Función para verificar solicitudes pendientes
    async function tieneSolicitudPendiente(tipo) {
        try {
            const response = await fetch('/verestatus');
            const data = await response.json();
            return data.some(s => s.tipo === tipo && s.estado === 'PENDIENTE');
        } catch (error) {
            console.error('Error:', error);
            return false;
        }
    }

    // Función para obtener la fecha mínima permitida (mañana a medianoche)
    // Esto evita seleccionar fechas de hoy o del pasado.
    function obtenerFechaMinima() {
        const ahora = new Date();
        const manana = new Date(ahora);
        manana.setDate(ahora.getDate() + 1);
        manana.setHours(0, 0, 0, 0); // Establece la hora a medianoche de mañana
        return manana.toISOString().split('T')[0]; // Formato YYYY-MM-DD
    }

    // Función para validar fechas en tiempo real
    function validarFechas() {
        const fechaMin = obtenerFechaMinima();
        const inicio = new Date(fechaInicio.value);
        const fin = new Date(fechaFin.value);

        // Validar que la fecha de inicio no sea menor que la mínima permitida (mañana)
        if (fechaInicio.value && inicio < new Date(fechaMin)) {
            alert("❌ La fecha de inicio debe ser posterior a la fecha actual.");
            fechaInicio.value = '';
        }

        // Validar que la fecha de fin no sea menor que la mínima permitida (mañana)
        if (fechaFin.value && fin < new Date(fechaMin)) {
            alert("❌ La fecha de fin debe ser posterior a la fecha actual.");
            fechaFin.value = '';
        }

        // Validar que la fecha de fin no sea anterior a la de inicio
        if (fechaInicio.value && fechaFin.value && fin < inicio) {
            alert("❌ La fecha de fin no puede ser anterior a la fecha de inicio.");
            fechaFin.value = "";
        }
    }

    // Deshabilitar campos para VACACIONES y obtener días disponibles
    document.querySelectorAll('input[name="tipo"]').forEach(radio => {
        radio.addEventListener('change', async (e) => {
            const tipo = e.target.value;
            const pendiente = await tieneSolicitudPendiente(tipo);
            
            if (pendiente) {
                alert(`Ya tienes una solicitud de ${tipo} pendiente!`);
                e.target.checked = false;
                return;
            }

            const isVacaciones = tipo === 'VACACIONES';
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

    // Validación al enviar el formulario
    form.addEventListener("submit", async function (event) {
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

        if (tipo && await tieneSolicitudPendiente(tipo)) {
            alert(`No puedes enviar otra solicitud de ${tipo} con una pendiente!`);
            event.preventDefault();
            return;
        }

        const inicioDate = new Date(fechaInicioVal);
        const finDate = new Date(fechaFinVal);
        const diasSolicitados = Math.ceil((finDate - inicioDate) / (1000 * 60 * 60 * 24)) + 1;

        // Validar que las fechas sean posteriores a la fecha actual (mínimo mañana)
        const fechaMinima = new Date(obtenerFechaMinima());
        if (inicioDate < fechaMinima || finDate < fechaMinima) {
            alert("⚠️ Las fechas deben ser posteriores a la fecha actual.");
            event.preventDefault();
            return;
        }

        if (finDate < inicioDate) {
            alert("❌ La fecha de fin no puede ser anterior a la fecha de inicio.");
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

            // Validar archivo
            const tiposPermitidos = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf'];
            const extensionesPermitidas = ['jpg', 'jpeg', 'png', 'pdf'];
            const archivoSubidoObj = archivo.files[0];
            const extension = archivoSubidoObj.name.split('.').pop().toLowerCase();

            if (!tiposPermitidos.includes(archivoSubidoObj.type) || !extensionesPermitidas.includes(extension)) {
                alert("❌ Formato no válido. Solo se permiten JPEG, PNG o PDF.");
                event.preventDefault();
                return;
            }
        }
    });
});

// Función para validar el archivo al seleccionarlo
function validarArchivo(input) {
    const tiposPermitidos = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf'];
    const extensionesPermitidas = ['jpg', 'jpeg', 'png', 'pdf'];
    
    if (input.files.length > 0) {
        const archivo = input.files[0];
        const extension = archivo.name.split('.').pop().toLowerCase();
        
        if (!tiposPermitidos.includes(archivo.type) || !extensionesPermitidas.includes(extension)) {
            alert("❌ Formato no válido. Solo se permiten: JPG, PNG, PDF");
            input.value = ""; // Limpia el input
        }
    }
}

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
