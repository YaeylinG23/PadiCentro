document.addEventListener('DOMContentLoaded', () => {
    // Función para mostrar/ocultar el dropdown
    window.toggleDropdownFiltroTipo = () => {
        document.getElementById("dropdownTipo").classList.toggle("show");
    };

    // Función para aplicar el filtro
    const filterByType = () => {
        const checkboxes = document.querySelectorAll('#dropdownTipo input[type="checkbox"]');
        const selectedTypes = Array.from(checkboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.value);
    
        document.querySelectorAll('tbody tr').forEach(row => {
            const tipo = row.getAttribute('data-tipo');
            if (selectedTypes.length === 0 || selectedTypes.includes(tipo)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    };

    // Función que aplica filtro + cierra el dropdown
    const filterAndClose = () => {
        filterByType();
        document.getElementById("dropdownTipo").classList.remove("show"); // ✅ Cierra el menú
    };

    // Cerrar dropdown al hacer clic fuera
    window.addEventListener('click', (e) => {
        if (!e.target.closest('.dropdown')) {
            document.getElementById("dropdownTipo").classList.remove("show");
        }
    });

    // Vincular eventos a los checkboxes (ahora con cierre automático)
    document.querySelectorAll('#dropdownTipo input[type="checkbox"]').forEach(checkbox => {
        checkbox.addEventListener('change', filterAndClose); // ✅ Usa filterAndClose
    });

    // Aplicar filtro inicial
    filterByType();
});