// Lógica del Panel de Administración Privado - Veeduría Ciudadana Cicuco Transparente

document.addEventListener('DOMContentLoaded', () => {
    initAdminTabs();
    initContractForm();
    initContractActions();
    initReportUpdates();
    initRejectReportModal();
    initDeleteConfirmModal();
    initApproveReportModal();
    initSettingsForm();
    initAdminEscapeKey();
    if (window.lucide) {
        lucide.createIcons();
    }
});

// 1. Navegación de pestañas internas del Admin con soporte de Hash en URL
function initAdminTabs() {
    const tabBtns = document.querySelectorAll('.admin-tab-btn');
    const tabPanes = document.querySelectorAll('.admin-tab-pane');

    function activateTab(target) {
        tabBtns.forEach(b => {
            if (b.dataset.target === target) {
                b.classList.add('bg-blue-900', 'text-white');
                b.classList.remove('text-slate-600', 'hover:bg-slate-100');
            } else {
                b.classList.remove('bg-blue-900', 'text-white');
                b.classList.add('text-slate-600', 'hover:bg-slate-100');
            }
        });

        tabPanes.forEach(pane => {
            if (pane.id === target) {
                pane.classList.remove('hidden');
            } else {
                pane.classList.add('hidden');
            }
        });

        history.replaceState(null, null, `#${target}`);
        if (window.lucide) {
            lucide.createIcons();
        }
    }

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.dataset.target;
            if (target) activateTab(target);
        });
    });

    // Detectar hash al cargar la página
    const currentHash = window.location.hash.replace('#', '');
    if (currentHash && document.getElementById(currentHash)) {
        activateTab(currentHash);
    }
}

// 2. Formulario para Subir / Crear Nuevo Contrato
function initContractForm() {
    const form = document.getElementById('admin-contract-form');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = form.querySelector('button[type="submit"]');
        const origText = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = 'Publicando Contrato...';

        const formData = new FormData(form);

        try {
            const res = await fetch('/api/admin/contracts/create', {
                method: 'POST',
                body: formData
            });

            const data = await res.json();
            if (data.success) {
                alert('¡Contrato subido y publicado exitosamente en el catálogo público!');
                window.location.hash = '#admin-pane-contracts';
                window.location.reload();
            } else {
                alert('Error al publicar contrato: ' + (data.error || 'Verifica los campos ingresados.'));
            }
        } catch (err) {
            console.error('Error al subir contrato:', err);
            alert('Error de conexión con el servidor.');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = origText;
        }
    });
}

// 3. Acciones de Contratos (Editar / Eliminar)
function initContractActions() {
    // Eliminar contrato con modal personalizado
    document.querySelectorAll('.btn-delete-contract').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const id = btn.dataset.id;
            const code = btn.dataset.code;
            openDeleteConfirmModal({
                title: `¿Eliminar Contrato [${code}]?`,
                subtitle: 'Esta acción retirará permanentemente el contrato del catálogo público.',
                itemName: `Contrato: ${code}`,
                warning: 'Se eliminarán los registros públicos, el historial de fiscalización y los documentos vinculados.',
                onConfirm: async () => {
                    const res = await fetch(`/api/admin/contracts/${id}/delete`, {
                        method: 'POST'
                    });
                    const data = await res.json();
                    if (data.success) {
                        window.location.hash = '#admin-pane-contracts';
                        window.location.reload();
                    } else {
                        alert('Error al eliminar: ' + (data.error || 'Error desconocido'));
                    }
                }
            });
        });
    });

    // Modal de edición rápida
    const editModal = document.getElementById('admin-edit-contract-modal');
    const closeEditBtn = document.getElementById('btn-close-edit-modal');
    const cancelEditBtn = document.getElementById('btn-cancel-edit-modal');
    const editForm = document.getElementById('admin-edit-contract-form');

    if (!editModal || !editForm) return;

    function closeEdit() {
        editModal.classList.add('hidden');
        editModal.classList.remove('flex');
    }

    if (closeEditBtn) closeEditBtn.addEventListener('click', closeEdit);
    if (cancelEditBtn) cancelEditBtn.addEventListener('click', closeEdit);

    editModal.addEventListener('click', (e) => {
        if (e.target === editModal) closeEdit();
    });

    document.querySelectorAll('.btn-edit-contract').forEach(btn => {
        btn.addEventListener('click', async () => {
            const id = btn.dataset.id;
            try {
                const res = await fetch(`/api/contracts/${id}`);
                if (!res.ok) {
                    alert('No se pudo cargar la información del contrato.');
                    return;
                }
                const c = await res.json();
                if (c && !c.error) {
                    document.getElementById('edit-contract-id').value = c.id;
                    document.getElementById('edit-code').value = c.code || '';
                    document.getElementById('edit-title').value = c.title || '';
                    document.getElementById('edit-sector').value = c.sector || 'Infraestructura y Vías';
                    document.getElementById('edit-entity').value = c.entity || 'Alcaldía Municipal de Cicuco';
                    document.getElementById('edit-contractor').value = c.contractor || '';
                    document.getElementById('edit-amount').value = c.amount || '';
                    document.getElementById('edit-progress-phys').value = c.progress_physical || 0;
                    document.getElementById('edit-progress-fin').value = c.progress_financial || 0;
                    document.getElementById('edit-status').value = c.status || 'En Ejecución';
                    document.getElementById('edit-status-type').value = c.status_type || 'info';
                    document.getElementById('edit-inspection').value = c.last_inspection || '';
                    document.getElementById('edit-summary').value = c.summary || '';
                    document.getElementById('edit-external-link').value = c.external_link || '';

                    editModal.classList.remove('hidden');
                    editModal.classList.add('flex');
                    if (window.lucide) lucide.createIcons();
                } else {
                    alert(c.error || 'Error al obtener datos del contrato.');
                }
            } catch (err) {
                console.error(err);
                alert('No se pudo conectar con el servidor.');
            }
        });
    });

    editForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = document.getElementById('edit-contract-id').value;
        const submitBtn = editForm.querySelector('button[type="submit"]');
        const origText = submitBtn.innerHTML;

        submitBtn.disabled = true;
        submitBtn.textContent = 'Guardando Cambios...';

        const formData = new FormData(editForm);

        try {
            const res = await fetch(`/api/admin/contracts/${id}/edit`, {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            if (data.success) {
                alert('¡Contrato modificado exitosamente!');
                window.location.hash = '#admin-pane-contracts';
                window.location.reload();
            } else {
                alert('Error al modificar: ' + (data.error || 'Verifica los campos ingresados.'));
            }
        } catch (err) {
            console.error(err);
            alert('Error de conexión con el servidor.');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = origText;
        }
    });
}

// 4. Actualización y Eliminación de Denuncias
function initReportUpdates() {
    // Formulario de actualización de estado y notas
    document.querySelectorAll('.report-update-form').forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const id = form.dataset.reportId;
            const statusSelect = form.querySelector('select[name="status"]');
            const notesInput = form.querySelector('input[name="admin_notes"]');
            const submitBtn = form.querySelector('button[type="submit"]');

            submitBtn.disabled = true;
            submitBtn.textContent = 'Guardando...';

            const formData = new FormData();
            formData.append('status', statusSelect.value);
            formData.append('admin_notes', notesInput.value);

            try {
                const res = await fetch(`/api/admin/reports/${id}/update`, {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                if (data.success) {
                    submitBtn.classList.remove('bg-blue-900');
                    submitBtn.classList.add('bg-emerald-600');
                    submitBtn.textContent = '¡Guardado!';
                    setTimeout(() => {
                        window.location.hash = '#admin-pane-reports';
                        window.location.reload();
                    }, 600);
                } else {
                    alert('Error al actualizar estado: ' + (data.error || 'Error desconocido'));
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Actualizar Estado';
                }
            } catch (err) {
                console.error(err);
                alert('Error al conectar con el servidor.');
                submitBtn.disabled = false;
                submitBtn.textContent = 'Actualizar Estado';
            }
        });
    });

    // Eliminar Denuncia con modal elegante
    document.querySelectorAll('.btn-delete-report').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const id = btn.dataset.id;
            const code = btn.dataset.code || '';
            const subject = btn.dataset.subject || '';

            openDeleteConfirmModal({
                title: `¿Eliminar Denuncia [${code}]?`,
                subtitle: 'Esta acción borrará de forma definitiva el radicado de la base de datos.',
                itemName: `Radicado: ${code}${subject ? ' — ' + subject : ''}`,
                warning: 'Se eliminarán permanentemente el radicado ciudadano, las notas del veedor y los archivos de prueba adjuntos de forma irreversible.',
                onConfirm: async () => {
                    const res = await fetch(`/api/admin/reports/${id}/delete`, {
                        method: 'POST'
                    });
                    const data = await res.json();
                    if (data.success) {
                        window.location.hash = '#admin-pane-reports';
                        window.location.reload();
                    } else {
                        alert('Error al eliminar denuncia: ' + (data.error || 'Error desconocido'));
                    }
                }
            });
        });
    });
}

// 4.1 Modal Personalizado para Rechazo de Denuncias
function initRejectReportModal() {
    const modal = document.getElementById('admin-reject-report-modal');
    const closeBtn = document.getElementById('btn-close-reject-modal');
    const cancelBtn = document.getElementById('btn-cancel-reject-modal');
    const form = document.getElementById('admin-reject-report-form');
    const idInput = document.getElementById('reject-report-id');
    const codeEl = document.getElementById('reject-report-code');
    const catEl = document.getElementById('reject-report-category');
    const subEl = document.getElementById('reject-report-subject');
    const reasonInput = document.getElementById('reject-report-reason');
    const submitBtn = document.getElementById('btn-submit-reject');

    if (!modal || !form) return;

    function closeModal() {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }

    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    if (cancelBtn) cancelBtn.addEventListener('click', closeModal);

    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });

    document.querySelectorAll('.btn-reject-report').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const id = btn.dataset.id;
            const code = btn.dataset.code || '';
            const category = btn.dataset.category || 'Denuncia Ciudadana';
            const subject = btn.dataset.subject || 'Sin asunto especificado';

            idInput.value = id;
            if (codeEl) codeEl.textContent = code;
            if (catEl) catEl.textContent = category;
            if (subEl) subEl.textContent = subject;

            reasonInput.value = 'Denuncia desestimada o no procedente tras evaluación técnica del comité veedor.';

            modal.classList.remove('hidden');
            modal.classList.add('flex');
            reasonInput.focus();
            if (window.lucide) lucide.createIcons();
        });
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = idInput.value;
        const reason = reasonInput.value.trim();
        if (!reason) {
            reasonInput.focus();
            return;
        }

        const origHtml = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> Guardando rechazo...';
        if (window.lucide) lucide.createIcons();

        const formData = new FormData();
        formData.append('reason', reason);

        try {
            const res = await fetch(`/api/admin/reports/${id}/reject`, {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            if (data.success) {
                closeModal();
                window.location.hash = '#admin-pane-reports';
                window.location.reload();
            } else {
                alert('Error al rechazar denuncia: ' + (data.error || 'Error desconocido'));
                submitBtn.disabled = false;
                submitBtn.innerHTML = origHtml;
                if (window.lucide) lucide.createIcons();
            }
        } catch (err) {
            console.error(err);
            alert('Error de conexión al rechazar denuncia.');
            submitBtn.disabled = false;
            submitBtn.innerHTML = origHtml;
            if (window.lucide) lucide.createIcons();
        }
    });
}

// 4.2 Modal Personalizado para Confirmar Eliminaciones
let pendingDeleteAction = null;

function openDeleteConfirmModal({ title, subtitle, itemName, warning, onConfirm }) {
    const modal = document.getElementById('admin-delete-confirm-modal');
    if (!modal) return;

    if (title) document.getElementById('delete-modal-title').textContent = title;
    if (subtitle) document.getElementById('delete-modal-subtitle').textContent = subtitle;
    if (itemName) document.getElementById('delete-modal-item-name').textContent = itemName;
    if (warning) document.getElementById('delete-modal-warning').textContent = warning;

    pendingDeleteAction = onConfirm;

    modal.classList.remove('hidden');
    modal.classList.add('flex');
    if (window.lucide) lucide.createIcons();
}

function initDeleteConfirmModal() {
    const modal = document.getElementById('admin-delete-confirm-modal');
    const closeBtn = document.getElementById('btn-close-delete-modal');
    const cancelBtn = document.getElementById('btn-cancel-delete-modal');
    const confirmBtn = document.getElementById('btn-confirm-delete-action');

    if (!modal || !confirmBtn) return;

    function closeModal() {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
        pendingDeleteAction = null;
    }

    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    if (cancelBtn) cancelBtn.addEventListener('click', closeModal);

    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });

    confirmBtn.addEventListener('click', async () => {
        if (typeof pendingDeleteAction === 'function') {
            const origHtml = confirmBtn.innerHTML;
            confirmBtn.disabled = true;
            confirmBtn.innerHTML = '<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> Eliminando...';
            if (window.lucide) lucide.createIcons();
            try {
                await pendingDeleteAction();
            } finally {
                confirmBtn.disabled = false;
                confirmBtn.innerHTML = origHtml;
                if (window.lucide) lucide.createIcons();
            }
        }
    });
}

// 5. Configuración del Sistema (Correo y Contraseña)
function initSettingsForm() {
    const form = document.getElementById('admin-settings-form');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = form.querySelector('button[type="submit"]');
        const origText = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Guardando...';

        const formData = new FormData(form);

        try {
            const res = await fetch('/api/admin/settings/update', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            if (data.success) {
                alert('¡Configuración actualizada con éxito!');
                window.location.hash = '#admin-pane-settings';
                window.location.reload();
            } else {
                alert('Error: ' + (data.error || 'No se pudo actualizar'));
            }
        } catch (err) {
            console.error(err);
            alert('Error al guardar ajustes.');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = origText;
        }
    });
}

// 6. Modal de Aprobación de Denuncias para Catálogo de Obras
function initApproveReportModal() {
    const modal = document.getElementById('admin-approve-modal');
    const closeBtn = document.getElementById('btn-close-approve-modal');
    const cancelBtn = document.getElementById('btn-cancel-approve-modal');
    const form = document.getElementById('admin-approve-form');

    if (!modal || !form) return;

    function closeModal() {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }

    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    if (cancelBtn) cancelBtn.addEventListener('click', closeModal);

    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });

    document.querySelectorAll('.btn-open-approve-modal').forEach(btn => {
        btn.addEventListener('click', async () => {
            const id = btn.dataset.id;
            try {
                const res = await fetch(`/api/admin/reports/${id}/details`);
                const data = await res.json();
                if (data.success && data.report) {
                    const r = data.report;
                    document.getElementById('approve-report-id').value = r.id;
                    document.getElementById('approve-orig-code').textContent = r.code;
                    document.getElementById('approve-orig-location').textContent = r.location;
                    document.getElementById('approve-orig-citizen').textContent = r.is_anonymous ? 'Anónimo Protegido' : (r.citizen_name || 'Ciudadano');

                    // Si ya tenía un contrato asociado en el catálogo, cargar los datos actuales de ese contrato
                    let existingContract = null;
                    if (r.approved_contract_id) {
                        try {
                            const cRes = await fetch(`/api/contracts/${r.approved_contract_id}`);
                            if (cRes.ok) {
                                const cData = await cRes.json();
                                if (cData && !cData.error) {
                                    existingContract = cData;
                                }
                            }
                        } catch (errC) {
                            console.log('No se pudo cargar contrato asociado, se usarán datos de reporte.');
                        }
                    }

                    if (existingContract) {
                        document.getElementById('approve-code').value = existingContract.code || `OBR-${r.code}`;
                        document.getElementById('approve-title').value = existingContract.title || r.subject;
                        document.getElementById('approve-sector').value = existingContract.sector || 'Infraestructura y Vías';
                        document.getElementById('approve-entity').value = existingContract.entity || 'Alcaldía Municipal de Cicuco';
                        document.getElementById('approve-contractor').value = existingContract.contractor || 'Por Identificar / En Verificación';
                        document.getElementById('approve-amount').value = existingContract.amount || 'En Auditoría Ciudadana';
                        document.getElementById('approve-progress-phys').value = existingContract.progress_physical || 0;
                        document.getElementById('approve-progress-fin').value = existingContract.progress_financial || 0;
                        document.getElementById('approve-status').value = existingContract.status || 'Alerta Ciudadana en Fiscalización';
                        document.getElementById('approve-status-type').value = existingContract.status_type || 'warning';
                        document.getElementById('approve-inspection').value = existingContract.last_inspection || 'Inspección Comunitaria Reciente';
                        document.getElementById('approve-summary').value = existingContract.summary || `Ubicación: ${r.location}\n\nHechos denunciados por la comunidad: ${r.description}`;
                    } else {
                        document.getElementById('approve-code').value = `OBR-${r.code}`;
                        document.getElementById('approve-title').value = r.subject;

                        // Mapear categoría a sector
                        const sectorSelect = document.getElementById('approve-sector');
                        const cat = r.category || '';
                        if (cat.includes('Obra') || cat.includes('Pavimentación')) {
                            sectorSelect.value = 'Infraestructura y Vías';
                        } else if (cat.includes('PAE') || cat.includes('Alimentación')) {
                            sectorSelect.value = 'Educación y Nutrición';
                        } else if (cat.includes('Salud') || cat.includes('Hospital')) {
                            sectorSelect.value = 'Salud Pública';
                        } else if (cat.includes('Acueducto') || cat.includes('Alcantarillado')) {
                            sectorSelect.value = 'Agua y Saneamiento';
                        } else {
                            sectorSelect.value = 'Infraestructura y Vías';
                        }

                        document.getElementById('approve-entity').value = 'Alcaldía Municipal de Cicuco';
                        document.getElementById('approve-contractor').value = 'Por Identificar / En Verificación';
                        document.getElementById('approve-amount').value = 'En Auditoría Ciudadana';
                        document.getElementById('approve-progress-phys').value = 0;
                        document.getElementById('approve-progress-fin').value = 0;
                        document.getElementById('approve-status').value = 'Alerta Ciudadana en Fiscalización';
                        document.getElementById('approve-status-type').value = 'warning';
                        document.getElementById('approve-inspection').value = 'Inspección Comunitaria Reciente';
                        document.getElementById('approve-summary').value = `Ubicación: ${r.location}\n\nHechos denunciados por la comunidad: ${r.description}`;
                    }

                    const evNotice = document.getElementById('approve-evidence-link-name');
                    if (r.evidence_file) {
                        evNotice.textContent = r.evidence_file;
                    } else {
                        evNotice.textContent = 'Sin archivo adjunto';
                    }

                    modal.classList.remove('hidden');
                    modal.classList.add('flex');
                    if (window.lucide) lucide.createIcons();
                }
            } catch (err) {
                console.error(err);
                alert('No se pudo cargar la información del reporte.');
            }
        });
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = document.getElementById('approve-report-id').value;
        const submitBtn = form.querySelector('button[type="submit"]');
        const origText = submitBtn.innerHTML;

        submitBtn.disabled = true;
        submitBtn.innerHTML = 'Publicando en Catálogo...';

        const formData = new FormData(form);

        try {
            const res = await fetch(`/api/admin/reports/${id}/approve`, {
                method: 'POST',
                body: formData
            });

            const data = await res.json();
            if (data.success) {
                alert(data.message || '¡Reporte aprobado y publicado exitosamente en el Catálogo de Obras!');
                window.location.hash = '#admin-pane-reports';
                window.location.reload();
            } else {
                alert('Error al aprobar: ' + (data.error || 'Error desconocido'));
            }
        } catch (err) {
            console.error(err);
            alert('Error de conexión con el servidor.');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = origText;
        }
    });
}

// 7. Tecla Escape para cerrar modales del Admin
function initAdminEscapeKey() {
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const modals = [
                document.getElementById('admin-edit-contract-modal'),
                document.getElementById('admin-approve-modal'),
                document.getElementById('admin-reject-report-modal'),
                document.getElementById('admin-delete-confirm-modal')
            ];
            modals.forEach(m => {
                if (m && !m.classList.contains('hidden')) {
                    m.classList.add('hidden');
                    m.classList.remove('flex');
                }
            });
        }
    });
}
