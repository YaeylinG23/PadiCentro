document.addEventListener("DOMContentLoaded", function() {
    function getSelectedIdsFromURL() {
        const params = new URLSearchParams(window.location.search);
        const ids = params.get('filter_ids') || '';
        return ids.split(',').filter(id => id !== '').map(id => parseInt(id));
    }

    function toggleDropdown() {
        document.getElementById("dropdownMenu").classList.toggle("show");
    }

    function filterTable() {
        const selectedIds = Array.from(document.querySelectorAll('#dropdownMenu .empleado-checkbox:checked'))
                                .map(cb => cb.value);
        window.location.search = `?filter_ids=${selectedIds.join(',')}`;
    }

    // Restaurar checkboxes desde la URL
    const selectedIds = getSelectedIdsFromURL();
    selectedIds.forEach(id => {
        const checkbox = document.querySelector(`.empleado-checkbox[value="${id}"]`);
        if (checkbox) checkbox.checked = true;
    });

    // Event listeners
    document.querySelector('.dropbtn').addEventListener('click', toggleDropdown);
    document.querySelectorAll('#dropdownMenu .empleado-checkbox').forEach(cb => {
        cb.addEventListener('change', filterTable);
    });

    // Cerrar dropdown al hacer clic fuera
    window.onclick = function(e) {
        if (!e.target.closest('.dropdown')) {
            document.querySelectorAll('.dropdown-content').forEach(dropdown => {
                dropdown.classList.remove('show');
            });
        }
    }
});
