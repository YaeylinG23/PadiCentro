let horarioTemplate; // Declaración global

// Función global para formatear fechas
function formatDateForInput(dateString) {
  if (!dateString) return "";
  return dateString.includes("T") ? dateString.split("T")[0] : dateString;
}

// Función global para eliminar registros
function eliminarRegistro(id_uem) {
    fetch(`/eliminar_colaborador/${id_uem}`, { method: 'DELETE' })
        .then(response => {
            if (!response.ok) throw new Error('Error en la respuesta del servidor');
            return response.json();
        })
        .then(data => {
            if (data.success) {
                location.reload(); // Recargar solo si la eliminación fue exitosa
            } else {
                alert('Error al eliminar: ' + (data.error || 'Desconocido'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error de conexión');
        });
}


document.addEventListener("DOMContentLoaded", function() {
  // Obtener referencias para el manejo de horarios
  const addHorarioBtn = document.getElementById('addHorario');
  const horarioContainer = document.getElementById('horarioContainer');
  horarioTemplate = document.querySelector('.horario');
  
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

  // Unificar la validación y el envío del formulario (para agregar o actualizar)
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

  // Función que filtra las filas de la tabla
  function filterTable() {
    // Obtener los IDs seleccionados de los checkboxes
    const selectedIds = Array.from(document.querySelectorAll('.empleado-checkbox:checked'))
                              .map(cb => parseInt(cb.value));
    console.log("IDs seleccionados:", selectedIds);

    // Recorrer cada fila y mostrarla u ocultarla según corresponda
    document.querySelectorAll('tbody tr').forEach(row => {
      const rowId = parseInt(row.dataset.id);
      if (selectedIds.length === 0 || selectedIds.includes(rowId)) {
        row.style.display = '';
      } else {
        row.style.display = 'none';
      }
    });
  }

  // Asignar el listener a cada checkbox
  document.querySelectorAll('.empleado-checkbox').forEach(cb => {
    cb.addEventListener('change', filterTable);
  });

  // Llamamos a filterTable al cargar la página para que se aplique el estado guardado
  filterTable();
});

// Listener global para botones de editar y eliminar
document.addEventListener('click', function(e) {
  const btnEditar = e.target.closest('.btn-editar');
  if (btnEditar) {
    const id_uem = btnEditar.getAttribute('data-id');
    console.log("Botón editar clickeado, id:", id_uem);
    abrirModalEditar(id_uem);
  }
  
  const btnEliminar = e.target.closest('.btn-eliminar');
  if (btnEliminar) {
    const id_uem = btnEliminar.getAttribute('data-id');
    openDeleteModal(id_uem); // ✅ Ahora solo abre el modal de confirmación
  }
});

function abrirModalEditar(id_uem) {
  console.log("Iniciando edición para id:", id_uem);
  document.getElementById('myModal').style.display = 'none';

  fetch(`/obtener_colaborador/${id_uem}`)
    .then(response => response.json())
    .then(data => {
      console.log("Respuesta del servidor:", data);
      if (data.error) {
        alert("Error al obtener datos del colaborador: " + data.error);
        return;
      }
      const colaborador = data.colaborador;
      if (!colaborador || Object.keys(colaborador).length === 0) {
        alert("No se encontró el colaborador.");
        return;
      }
      
      // Asignación de valores al formulario del modal
      document.querySelector('#myModal input[name="nombre_completo"]').value = colaborador.nombre_completo || "";
      document.querySelector('#myModal input[name="fecha_nacimiento"]').value = formatDateForInput(colaborador.fecha_nacimiento);
      document.querySelector('#myModal input[name="direccion"]').value = colaborador.direccion || "";
      document.querySelector('#myModal input[name="telefono"]').value = colaborador.telefono || "";
      document.querySelector('#myModal input[name="email"]').value = colaborador.email || "";
      document.querySelector('#myModal input[name="departamento"]').value = colaborador.departamento || "";
      document.querySelector('#myModal input[name="fecha_contratacion"]').value = formatDateForInput(colaborador.fecha_contratacion);
      document.querySelector('#myModal input[name="usuario"]').value = colaborador.usuario || "";
      document.querySelector('#myModal input[name="contrasena"]').value = colaborador.contrasena || "";
      document.querySelector('#myModal input[name="id_uem"]').value = colaborador.id_uem || "";
  
      // Limpiar el contenedor de horarios
      const container = document.getElementById('horarioContainer');
      container.innerHTML = '';
      
      // Usar la variable global 'horarioTemplate' para clonar la plantilla
      data.horarios.forEach(horario => {
        const clone = horarioTemplate.cloneNode(true);
        clone.querySelector('input[name="horario_entrada_campo[]"]').value = horario.horario_entrada || "";
        clone.querySelector('input[name="horario_salida_campo[]"]').value = horario.horario_salida || "";
        
        if (horario.dias) {
          horario.dias.forEach(dia => {
            const checkbox = clone.querySelector(`input[value="${dia}"]`);
            if (checkbox) checkbox.checked = true;
          });
        }
        
        // Asegurar que exista el botón de eliminar
        if (!clone.querySelector('.btn-delete')) {
          const deleteBtn = document.createElement("button");
          deleteBtn.type = "button";
          deleteBtn.textContent = "Eliminar";
          deleteBtn.classList.add("btn-delete");
          clone.appendChild(deleteBtn);
        }
        
        container.appendChild(clone);
      });
  
      // Mostrar el modal con los datos cargados
      document.getElementById('myModal').style.display = 'block';
    })
    .catch(error => {
      console.error("Error al obtener colaborador:", error);
      alert("Error al obtener datos del colaborador.");
    });
}
function descargarUsuarios() {
  window.location.href = "/descargar_usuarios";
}