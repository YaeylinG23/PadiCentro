document.addEventListener("DOMContentLoaded", function() {
    // Obtener referencias para el manejo de horarios
    const addHorarioBtn = document.getElementById('addHorario');
    const horarioContainer = document.getElementById('horarioContainer');
    
    // Agregar un nuevo bloque de horario
    addHorarioBtn.addEventListener('click', function() {
        const originalHorario = document.querySelector('.horario');
        const horarioClone = originalHorario.cloneNode(true);

        // Limpiar valores de inputs y checkboxes
        horarioClone.querySelectorAll('input[type="time"]').forEach(input => input.value = '');
        horarioClone.querySelectorAll('input[type="checkbox"]').forEach(checkbox => checkbox.checked = false);

        // Agregar botón Eliminar si aún no existe
        let deleteBtn = horarioClone.querySelector('.btn-delete');
        if (!deleteBtn) {
            deleteBtn = document.createElement("button");
            deleteBtn.type = "button";
            deleteBtn.classList.add("btn-delete");
            deleteBtn.textContent = "Eliminar";
            horarioClone.appendChild(deleteBtn);
        }

        horarioContainer.appendChild(horarioClone);
    });

    // Eliminar un bloque de horario
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('btn-delete')) {
            const horario = e.target.closest('.horario');
            const allHorarios = document.querySelectorAll('.horario');
            if (allHorarios.length > 1) horario.remove();
            else alert("⚠️ No puedes eliminar el horario principal.");
        }
    });

    // Restablecer todos los horarios
    document.getElementById('resetHorario').addEventListener('click', function() {
        document.querySelectorAll('.horario').forEach((horario, index) => {
            horario.querySelectorAll('input').forEach(input => {
                if (input.type === 'time') input.value = '';
                if (input.type === 'checkbox') input.checked = false;
            });
            if (index === 0) {
                const deleteBtn = horario.querySelector('.btn-delete');
                if (deleteBtn) deleteBtn.remove();
            }
        });
    });

    // Unificar la validación y el envío del formulario (tanto para agregar como para actualizar)
    const form = document.getElementById("empleadoForm");
    if (form) {
        form.addEventListener("submit", function(e) {
            e.preventDefault();
            let hasErrors = false;
            const horarios = [];

            // Validar cada bloque de horario
            document.querySelectorAll(".horario").forEach((horario, index) => {
                const entrada = horario.querySelector("input[name='horario_entrada_campo[]']").value;
                const salida = horario.querySelector("input[name='horario_salida_campo[]']").value;
                const dias = Array.from(horario.querySelectorAll("input[name='dias[]']:checked"))
                                .map(checkbox => checkbox.value);

                if (!entrada || !salida || dias.length === 0) {
                    alert(`⚠️ Horario ${index + 1}: Completa todos los campos!`);
                    hasErrors = true;
                    return;
                }

                horarios.push({ 
                    horario_entrada: entrada, 
                    horario_salida: salida, 
                    dias: dias 
                });
            });

            if (hasErrors || horarios.length === 0) {
                alert("¡Agrega al menos un horario válido!");
                return;
            }

            // Actualizar el campo oculto (opcional)
            document.getElementById("horarios_data").value = JSON.stringify(horarios);

            const id_uem = document.querySelector('input[name="id_uem"]').value;
            const url = id_uem ? `/actualizar_colaborador/${id_uem}` : '/añadir_empleados';
            const method = id_uem ? 'PUT' : 'POST';

            // Recopilar los datos del formulario
            const formData = {
                nombre_completo: document.getElementById('nombre').value,
                fecha_nacimiento: document.getElementById('nacimiento').value,
                direccion: document.getElementById('direccion').value,
                telefono: document.getElementById('telefono').value,
                email: document.getElementById('email').value,
                departamento: document.getElementById('departamento').value,
                fecha_contratacion: document.getElementById('contratacion').value,
                usuario: document.getElementById('usuario').value,
                contrasena: document.getElementById('contrasena').value,
                horarios: horarios
            };

            if (id_uem) formData.id_uem = id_uem;

            fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('myModal').style.display = 'none';
                    window.location.reload();
                } else {
                    alert('Error: ' + (data.error || 'Desconocido'));
                }
            })
            .catch(error => console.error('Error:', error));
        });
    } else {
        console.error("❌ El formulario no fue encontrado");
    }

    // ... [Otras funciones adicionales si las hubiere]
});

// Función para abrir el modal de edición y cargar datos del colaborador
function abrirModalEditar(id_uem) {
    document.getElementById('myModal').style.display = 'none';
    fetch(`/obtener_colaborador/${id_uem}`)
    .then(response => response.json())
    .then(data => {
        if(data.error){
            alert("Error al obtener datos del colaborador: " + data.error);
            return;
        }
        const colaborador = data.colaborador;
        if (!colaborador || Object.keys(colaborador).length === 0) {
            alert("No se encontró el colaborador.");
            return;
        }
        document.querySelector('#myModal input[name="nombre_completo"]').value = colaborador.nombre_completo || "";
        document.querySelector('#myModal input[name="fecha_nacimiento"]').value = colaborador.fecha_nacimiento || "";
        document.querySelector('#myModal input[name="direccion"]').value = colaborador.direccion || "";
        document.querySelector('#myModal input[name="telefono"]').value = colaborador.telefono || "";
        document.querySelector('#myModal input[name="email"]').value = colaborador.email || "";
        document.querySelector('#myModal input[name="departamento"]').value = colaborador.departamento || "";
        document.querySelector('#myModal input[name="fecha_contratacion"]').value = colaborador.fecha_contratacion || "";
        document.querySelector('#myModal input[name="usuario"]').value = colaborador.usuario || "";
        document.querySelector('#myModal input[name="contrasena"]').value = colaborador.contrasena || "";
        document.querySelector('#myModal input[name="id_uem"]').value = colaborador.id_uem || "";

        // Llenar horarios en el modal
        const container = document.getElementById('horarioContainer');
        container.innerHTML = '';
        
        data.horarios.forEach(horario => {
            const clone = document.querySelector('.horario').cloneNode(true);
            clone.querySelector('input[name="horario_entrada_campo[]"]').value = horario.horario_entrada || "";
            clone.querySelector('input[name="horario_salida_campo[]"]').value = horario.horario_salida || "";
            
            if (horario.dias) {
                horario.dias.forEach(dia => {
                    const checkbox = clone.querySelector(`input[value="${dia}"]`);
                    if (checkbox) checkbox.checked = true;
                });
            }
            
            if (!clone.querySelector('.btn-delete')) {
                const deleteBtn = document.createElement("button");
                deleteBtn.type = "button";
                deleteBtn.textContent = "Eliminar";
                deleteBtn.classList.add("btn-delete");
                clone.appendChild(deleteBtn);
            }
            
            container.appendChild(clone);
        });

        document.getElementById('myModal').style.display = 'block';
    })
    .catch(error => {
        console.error("Error al obtener colaborador:", error);
        alert("Error al obtener datos del colaborador.");
    });
}


// Función para eliminar un colaborador
function eliminarRegistro(id_uem) {
    if (confirm('¿Estás seguro de eliminar este registro?')) {
        fetch(`/eliminar_colaborador/${id_uem}`, { method: 'DELETE' })
        .then(response => {
            if (!response.ok) throw new Error('Error en la respuesta del servidor');
            return response.json();
        })
        .then(data => {
            if (data.success) {
                document.getElementById('myModal').style.display = 'none';
                location.reload();
            } else {
                alert('Error al eliminar: ' + (data.error || ''));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error de conexión');
        });
    }
}

// Eventos para botones de editar y eliminar en la tabla
document.addEventListener('click', function(e) {
    if (e.target.closest('.btn-editar')) {
        const id_uem = e.target.closest('.btn-editar').getAttribute('data-id');
        abrirModalEditar(id_uem);
    }
    if (e.target.closest('.btn-eliminar')) {
        const id_uem = e.target.closest('.btn-eliminar').getAttribute('data-id');
        eliminarRegistro(id_uem);
    }
});
