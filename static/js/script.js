// Clonamos el template de horario para usarlo en la edición y creación
let horarioTemplate = document.querySelector('.horario');
if (horarioTemplate) {
  horarioTemplate = horarioTemplate.cloneNode(true);
}

// Funciones utilitarias
function formatDateForInput(dateString) {
  if (!dateString) return "";
  return dateString.includes("T") ? dateString.split("T")[0] : dateString;
}

function calcularHoras(entrada, salida) {
  const [hEntrada, mEntrada] = entrada.split(':').map(Number);
  const [hSalida, mSalida] = salida.split(':').map(Number);
  const minutosEntrada = hEntrada * 60 + mEntrada;
  const minutosSalida = hSalida * 60 + mSalida;
  let diferencia = (minutosSalida - minutosEntrada) / 60;
  if (diferencia < 0) diferencia += 24;
  return diferencia;
}

function validarHorarioEnTiempoReal(input) {
  const horario = input.closest('.horario');
  const entrada = horario.querySelector('input[name="horario_entrada_campo[]"]').value;
  const salida = horario.querySelector('input[name="horario_salida_campo[]"]').value;
  if (!entrada || !salida) return;
  const horas = calcularHoras(entrada, salida);
  if (horas < 4 || horas > 8) {
    alert(`⚠️ Horario no válido. Duración: ${horas.toFixed(2)}h. Debe ser entre 4 y 8 horas.`);
    input.value = '';
    input.focus();
  }
}

// Funciones de CRUD
function eliminarRegistro(id_uem) {
  if (!confirm('¿Estás seguro de eliminar este colaborador?')) return;
  fetch(`/eliminar_colaborador/${id_uem}`, { method: 'DELETE' })
    .then(response => {
      if (!response.ok) throw new Error('Error en la respuesta del servidor');
      return response.json();
    })
    .then(data => {
      if (data.success) location.reload();
      else alert('Error al eliminar: ' + (data.error || 'Desconocido'));
    })
    .catch(error => {
      console.error('Error:', error);
      alert('Error de conexión');
    });
}

// Funciones de filtrado
function configurarFiltroInstantaneo() {
  document.querySelectorAll('.empleado-checkbox').forEach(checkbox => {
    checkbox.addEventListener('change', function() {
      const selectedIds = Array.from(document.querySelectorAll('.empleado-checkbox:checked'))
        .map(chk => chk.value);
      document.querySelectorAll('tbody tr').forEach(row => {
        const rowId = row.getAttribute('data-id');
        row.style.display = selectedIds.length === 0 || selectedIds.includes(rowId) ? '' : 'none';
      });
    });
  });
}

// Funciones de edición
function abrirModalEditar(id_uem) {
  fetch(`/obtener_colaborador/${id_uem}`)
    .then(response => response.json())
    .then(data => {
      const colaborador = data.colaborador;
      const horarios = data.horarios;
      
      // Llenar datos del formulario
      document.getElementById('id_uem').value = colaborador.id_uem;
      document.getElementById('nombre').value = colaborador.nombre_completo;
      document.getElementById('nacimiento').value = formatDateForInput(colaborador.fecha_nacimiento);
      document.getElementById('direccion').value = colaborador.direccion;
      document.getElementById('telefono').value = colaborador.telefono;
      document.getElementById('email').value = colaborador.email;
      document.getElementById('departamento').value = colaborador.departamento;
      document.getElementById('contratacion').value = formatDateForInput(colaborador.fecha_contratacion);
      document.getElementById('usuario').value = colaborador.usuario;
      document.getElementById('contrasena').value = colaborador.contrasena;

      // Configurar horarios
      const horarioContainer = document.getElementById('horarioContainer');
      horarioContainer.innerHTML = '';
      horarios.forEach(horario => {
        const nuevoHorario = horarioTemplate.cloneNode(true);
        nuevoHorario.querySelector('.input-entrada').value = horario.horario_entrada;
        nuevoHorario.querySelector('.input-salida').value = horario.horario_salida;
        
        nuevoHorario.querySelectorAll('input[type="time"]').forEach(input => {
          input.addEventListener('input', () => validarHorarioEnTiempoReal(input));
        });

        const dias = horario.dias.map(dia => dia.trim().toLowerCase());
        nuevoHorario.querySelectorAll('.input-horario').forEach(checkbox => {
          checkbox.checked = dias.includes(checkbox.value.trim().toLowerCase());
        });

        horarioContainer.appendChild(nuevoHorario);
      });
      document.getElementById('myModal').style.display = 'block';
    })
    .catch(error => console.error('Error al obtener datos:', error));
}

// Configuración inicial
document.addEventListener("DOMContentLoaded", function() {
  configurarFiltroInstantaneo();
  
  // Configuración de horarios
  const addHorarioBtn = document.getElementById('addHorario');
  const horarioContainer = document.getElementById('horarioContainer');
  const originalHorario = document.querySelector('.horario');

  if (originalHorario) horarioTemplate = originalHorario.cloneNode(true);

  addHorarioBtn?.addEventListener('click', function() {
    const horarioClone = horarioTemplate.cloneNode(true);
    horarioClone.querySelectorAll('input[type="time"]').forEach(input => {
      input.value = '';
      input.addEventListener('input', () => validarHorarioEnTiempoReal(input));
    });
    horarioClone.querySelectorAll('input[type="checkbox"]').forEach(checkbox => checkbox.checked = false);
    
    if (!horarioClone.querySelector('.btn-delete')) {
      const deleteBtn = document.createElement("button");
      deleteBtn.type = "button";
      deleteBtn.className = "btn-delete";
      deleteBtn.textContent = "Eliminar";
      horarioClone.appendChild(deleteBtn);
    }
    horarioContainer.appendChild(horarioClone);
  });

  // Delegación de eventos
  document.addEventListener('click', function(e) {
    if (e.target.classList.contains('btn-delete')) {
      const horario = e.target.closest('.horario');
      const allHorarios = document.querySelectorAll('.horario');
      allHorarios.length > 1 ? horario.remove() : alert("⚠️ No puedes eliminar el horario principal.");
    }
    
    if (e.target.classList.contains('btn-editar')) {
      const id_uem = e.target.getAttribute('data-id');
      if (id_uem) abrirModalEditar(id_uem);
    }
  });

  // Manejo del formulario
  const form = document.getElementById("empleadoForm");
  form?.addEventListener("submit", function(e) {
    e.preventDefault();
    let hasErrors = false;
    const horarios = [];

    document.querySelectorAll(".horario").forEach((horario, index) => {
      const entrada = horario.querySelector("input[name='horario_entrada_campo[]']").value;
      const salida = horario.querySelector("input[name='horario_salida_campo[]']").value;
      const dias = Array.from(horario.querySelectorAll("input[name='dias[]']:checked"))
                       .map(checkbox => checkbox.value);

      if (!entrada || !salida || !dias.length) {
        alert(`⚠️ Horario ${index + 1}: Completa todos los campos!`);
        hasErrors = true;
      }

      const horas = calcularHoras(entrada, salida);
      if (horas < 4 || horas > 8) {
        alert(`⚠️ Horario ${index + 1}: Jornada inválida (${horas.toFixed(2)}h)`);
        hasErrors = true;
      }

      horarios.push({ horario_entrada: entrada, horario_salida: salida, dias: dias });
    });

    if (hasErrors || !horarios.length) return alert("¡Agrega al menos un horario válido!");

    const formData = {
      id_uem: document.querySelector('input[name="id_uem"]')?.value,
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

    const url = formData.id_uem ? `/actualizar_colaborador/${formData.id_uem}` : '/añadir_empleados';
    const method = formData.id_uem ? 'PUT' : 'POST';

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
});

// Funciones adicionales
function descargarUsuarios() {
  window.location.href = "/descargar_usuarios";
}