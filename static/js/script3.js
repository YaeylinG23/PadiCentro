document.addEventListener("DOMContentLoaded", function() {
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

    function restoreCheckboxes(selector, values) {
        values.forEach(value => {
            const checkbox = document.querySelector(`${selector}[value="${value}"]`);
            if (checkbox) checkbox.checked = true;
        });
    }

    const urlParams = new URLSearchParams(window.location.search);
    restoreCheckboxes('.empleado-checkbox', urlParams.get('filter_ids')?.split(',') || []);
    restoreCheckboxes('.tipo-checkbox', urlParams.get('filter_types')?.split(',') || []);
    restoreCheckboxes('.estado-checkbox', urlParams.get('filter_status')?.split(',') || []);

    document.querySelectorAll('.dropdown-content input, .dropdown-content2 input, .dropdown-content3 input').forEach(checkbox => {
        checkbox.addEventListener('change', updateFilters);
    });
});

function toggleDropdown(dropdownId) {
    // Cerrar otros dropdowns antes de abrir el seleccionado
    document.querySelectorAll('.dropdown-content, .dropdown-content2, .dropdown-content3').forEach(dropdown => {
        if (dropdown.id !== dropdownId) {
            dropdown.classList.remove("show");
        }
    });

    // Alternar el estado del dropdown seleccionado
    document.getElementById(dropdownId).classList.toggle("show");
}

// Cerrar dropdowns al hacer clic fuera
window.onclick = function(e) {
    if (!e.target.matches('.dropbtn') &&
        !e.target.matches('.dropbtn2') &&
        !e.target.matches('.dropbtn3')) {

        document.querySelectorAll('.dropdown-content, .dropdown-content2, .dropdown-content3').forEach(dropdown => {
            dropdown.classList.remove('show');
        });
    }
};

function descargarHistorialAdmin() {
    window.location.href = "/descargar_historial_admin";
}
