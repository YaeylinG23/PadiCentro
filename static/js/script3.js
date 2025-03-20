document.addEventListener("DOMContentLoaded", function() {
    // Función para actualizar filtros
    function updateFilters() {
        const selectedIds = Array.from(document.querySelectorAll('.empleado-checkbox:checked'))
                               .map(cb => cb.value).join(',');
        const selectedTypes = Array.from(document.querySelectorAll('.tipo-checkbox:checked'))
                                .map(cb => cb.value).join(',');
        const selectedStatus = Array.from(document.querySelectorAll('.estado-checkbox:checked'))
                                 .map(cb => cb.value).join(',');

        const params = new URLSearchParams();
        if (selectedIds) params.set('filter_ids', selectedIds);
        if (selectedTypes) params.set('filter_types', selectedTypes);
        if (selectedStatus) params.set('filter_status', selectedStatus);

        window.location.search = params.toString();
    }

    // Restaurar checkboxes guardados
    function restoreCheckboxes(selector, values) {
        values.forEach(value => {
            const checkbox = document.querySelector(`${selector}[value="${value}"]`);
            if (checkbox) checkbox.checked = true;
        });
    }

    // Cargar parámetros de URL
    const urlParams = new URLSearchParams(window.location.search);
    restoreCheckboxes('.empleado-checkbox', urlParams.get('filter_ids')?.split(',') || []);
    restoreCheckboxes('.tipo-checkbox', urlParams.get('filter_types')?.split(',') || []);
    restoreCheckboxes('.estado-checkbox', urlParams.get('filter_status')?.split(',') || []);

    // Event listeners para filtros
    document.querySelectorAll('.dropdown-content input, .dropdown-content2 input, .dropdown-content3 input').forEach(checkbox => {
        checkbox.addEventListener('change', updateFilters);
    });

    // Lógica de validación
    let currentSolicitudId = null;

    // Abrir modal de validación
    document.querySelectorAll('.btn-validar').forEach(btn => {
        btn.addEventListener('click', (e) => {
            currentSolicitudId = e.target.dataset.id;
            const tipo = e.target.dataset.tipo;
            const comentarioEmpleado = e.target.dataset.comentario; // Obtener el comentario del empleado
    
            // Actualizar campos del modal
            document.getElementById('tipoSolicitud').textContent = tipo;
            document.getElementById('fechaInicio').textContent = e.target.dataset.inicio;
            document.getElementById('fechaFin').textContent = e.target.dataset.fin;
            document.getElementById('comentarioEmpleado').textContent = comentarioEmpleado; // Mostrar el comentario del empleado
    
            // Llamar al endpoint para obtener la validación existente del admin
            fetch(`/obtener_validacion/${currentSolicitudId}`)
                .then(response => response.json())
                .then(data => {
                    // data: { validation_id, comentario, motivo_cambio }
                    document.getElementById('comentarioValidacion').value = data.comentario || '';
                    if (data.validation_id) {
                        // Si ya existe una validación, mostrar el campo para el motivo del cambio
                        document.getElementById('motivoContainer').style.display = 'block';
                        document.getElementById('comentarioMotivo').value = data.motivo_cambio || '';
                    } else {
                        // Si es la primera validación, ocultar el campo de motivo
                        document.getElementById('motivoContainer').style.display = 'none';
                        document.getElementById('comentarioMotivo').value = '';
                    }
                })
                .catch(err => {
                    console.error(err);
                    document.getElementById('comentarioValidacion').value = '';
                    document.getElementById('motivoContainer').style.display = 'none';
                    document.getElementById('comentarioMotivo').value = '';
                });
    
            // Mostrar el modal
            document.getElementById('validationModal').style.display = 'block';
        });
    });

    // Función para cerrar el modal
    window.closeValidationModal = () => {
        document.getElementById('validationModal').style.display = 'none';
        currentSolicitudId = null;
    };

    window.verJustificante = async () => {
        try {
            const response = await fetch(`/obtener_justificante/${currentSolicitudId}`);
            const data = await response.json();
            if (data.justificante) {
                const byteCharacters = atob(data.justificante);
                const byteNumbers = new Array(byteCharacters.length);
                for (let i = 0; i < byteCharacters.length; i++) {
                    byteNumbers[i] = byteCharacters.charCodeAt(i);
                }
                const byteArray = new Uint8Array(byteNumbers);
                const blob = new Blob([byteArray], { type: data.mime_type });
                const url = window.URL.createObjectURL(blob);
                window.open(url);
            }
        } catch (error) {
            alert('Error al cargar el justificante');
        }
    };

    window.enviarDecision = async (decision) => {
        const adminComment = document.getElementById('comentarioValidacion').value.trim();
        const motive = document.getElementById('comentarioMotivo').value.trim();
    
        if (adminComment === "") {
            alert("Debes escribir un comentario.");
            return;
        }
        if (document.getElementById('motivoContainer').style.display === 'block' && motive === "") {
            alert("Debes escribir un motivo del cambio.");
            return;
        }
    
        try {
            const payload = {
                estado: decision,
                comentario: adminComment,
                motivo_cambio: motive
            };
    
            const response = await fetch(`/actualizar_solicitud/${currentSolicitudId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
    
            if (response.ok) {
                closeValidationModal();
                location.reload();
            } else {
                const resData = await response.json();
                alert(resData.error || "Error al enviar la decisión");
            }
        } catch (error) {
            alert('Error al enviar la decisión');
        }
    };
    

    // Cerrar modal al hacer clic fuera de él
    document.getElementById('validationModal').addEventListener('click', (e) => {
        if (e.target === document.getElementById('validationModal')) {
            closeValidationModal();
        }
    });
});

// Funciones globales para dropdowns y otros
function toggleDropdown(dropdownId) {
    document.querySelectorAll('.dropdown-content, .dropdown-content2, .dropdown-content3').forEach(dropdown => {
        if (dropdown.id !== dropdownId) dropdown.classList.remove("show");
    });
    document.getElementById(dropdownId).classList.toggle("show");
}

window.onclick = function(e) {
    if (!e.target.matches('.dropbtn') && !e.target.matches('.dropbtn2') && !e.target.matches('.dropbtn3')) {
        document.querySelectorAll('.dropdown-content, .dropdown-content2, .dropdown-content3').forEach(dropdown => {
            dropdown.classList.remove('show');
        });
    }
};

function descargarHistorialAdmin() {
    window.location.href = "/descargar_historial_admin";
}
