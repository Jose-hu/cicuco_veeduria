// Lógica del frontend para Veeduría Ciudadana Cicuco Transparente

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initContractsFilter();
    initReportForm();
    initLookupModal();
    initAdminLoginModal();
    initTemplateModal();
    initContractDetailsModal();
    initGlobalEscapeKey();
    if (window.lucide) {
        lucide.createIcons();
    }
});

// Función universal y robusta para copiar texto al portapapeles
function copyTextToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        return navigator.clipboard.writeText(text);
    } else {
        const textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.style.position = "fixed";
        textArea.style.left = "-999999px";
        textArea.style.top = "-999999px";
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        return new Promise((resolve, reject) => {
            const successful = document.execCommand('copy');
            textArea.remove();
            if (successful) resolve();
            else reject(new Error('execCommand copy failed'));
        });
    }
}

// -------------------------------------------------------------
// 1. NAVEGACIÓN ENTRE CATÁLOGOS (Inicio, Contratos, Blindaje, Denuncias)
// -------------------------------------------------------------
function initNavigation() {
    const tabs = document.querySelectorAll('.catalog-tab');
    const sections = document.querySelectorAll('.catalog-content');

    function switchCatalog(targetId) {
        // Remover estado activo de todos los botones y secciones
        tabs.forEach(tab => {
            if (tab.dataset.target === targetId) {
                tab.classList.add('active', 'bg-blue-900', 'text-white', 'shadow-md');
                tab.classList.remove('bg-white', 'text-slate-700', 'hover:bg-slate-100');
            } else {
                tab.classList.remove('active', 'bg-blue-900', 'text-white', 'shadow-md');
                tab.classList.add('bg-white', 'text-slate-700', 'hover:bg-slate-100');
            }
        });

        sections.forEach(section => {
            if (section.id === targetId) {
                section.classList.add('active');
            } else {
                section.classList.remove('active');
            }
        });

        // Actualizar URL hash sin salto brusco si no es un acceso de admin
        if (targetId && targetId !== 'acceso-admin') {
            history.replaceState(null, null, `#${targetId}`);
        }
        window.scrollTo({ top: 0, behavior: 'smooth' });

        if (window.lucide) {
            lucide.createIcons();
        }
    }

    tabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            e.preventDefault();
            const target = tab.dataset.target;
            if (target) {
                switchCatalog(target);
            }
        });
    });

    // Detectar hash inicial en la URL
    const hash = window.location.hash.replace('#', '');
    if (hash === 'acceso-admin') {
        switchCatalog('catalogo-inicio');
        // El modal de login administrativo se abrirá en initAdminLoginModal()
    } else if (hash && document.getElementById(hash)) {
        switchCatalog(hash);
    } else {
        switchCatalog('catalogo-inicio');
    }

    // Botones internos de enlace a catálogos (ej. "Ver Contratos", "Radicar Denuncia")
    document.querySelectorAll('[data-switch-catalog]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const target = btn.dataset.switchCatalog;
            if (target) switchCatalog(target);
        });
    });
}

// -------------------------------------------------------------
// 2. FILTRADO Y BÚSQUEDA DE CONTRATOS
// -------------------------------------------------------------
function initContractsFilter() {
    const searchInput = document.getElementById('contract-search-input');
    const sectorFilter = document.getElementById('contract-sector-filter');
    const statusFilter = document.getElementById('contract-status-filter');
    const contractsGrid = document.getElementById('contracts-grid');
    const noResultsMsg = document.getElementById('contracts-no-results');
    const clearBtn = document.getElementById('btn-clear-contract-filters');

    if (!searchInput || !contractsGrid) return;

    function filterCards() {
        const query = searchInput.value.toLowerCase().trim();
        const selectedSector = sectorFilter ? sectorFilter.value : 'Todos';
        const selectedStatus = statusFilter ? statusFilter.value : 'Todos';

        const cards = contractsGrid.querySelectorAll('.contract-card');
        let visibleCount = 0;

        cards.forEach(card => {
            const code = (card.dataset.code || '').toLowerCase();
            const title = (card.dataset.title || '').toLowerCase();
            const contractor = (card.dataset.contractor || '').toLowerCase();
            const summary = (card.dataset.summary || '').toLowerCase();
            const sector = card.dataset.sector || '';
            const status = card.dataset.status || '';

            const matchesQuery = !query || code.includes(query) || title.includes(query) || contractor.includes(query) || summary.includes(query);
            const matchesSector = selectedSector === 'Todos' || sector === selectedSector;
            const matchesStatus = selectedStatus === 'Todos' || status === selectedStatus;

            if (matchesQuery && matchesSector && matchesStatus) {
                card.style.display = ''; // Restaura display original (flex)
                visibleCount++;
            } else {
                card.style.display = 'none';
            }
        });

        if (noResultsMsg) {
            noResultsMsg.style.display = visibleCount === 0 ? 'block' : 'none';
        }
    }

    searchInput.addEventListener('input', filterCards);
    if (sectorFilter) sectorFilter.addEventListener('change', filterCards);
    if (statusFilter) statusFilter.addEventListener('change', filterCards);

    if (clearBtn) {
        clearBtn.addEventListener('click', (e) => {
            e.preventDefault();
            searchInput.value = '';
            if (sectorFilter) sectorFilter.value = 'Todos';
            if (statusFilter) statusFilter.value = 'Todos';
            filterCards();
        });
    }
}

// -------------------------------------------------------------
// 3. FORMULARIO DE RADICACIÓN DE DENUNCIAS Y REPORTES
// -------------------------------------------------------------
function initReportForm() {
    const form = document.getElementById('citizen-report-form');
    const anonCheckbox = document.getElementById('is-anonymous-checkbox');
    const personalFields = document.getElementById('personal-info-fields');
    const modalSuccess = document.getElementById('report-success-modal');

    if (anonCheckbox && personalFields) {
        anonCheckbox.addEventListener('change', () => {
            if (anonCheckbox.checked) {
                personalFields.style.opacity = '0.4';
                personalFields.querySelectorAll('input').forEach(inp => {
                    inp.disabled = true;
                    inp.value = '';
                });
            } else {
                personalFields.style.opacity = '1';
                personalFields.querySelectorAll('input').forEach(inp => {
                    inp.disabled = false;
                });
            }
        });
    }

    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalBtnHtml = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = `
            <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
            </svg>
            Procesando Radicación Oficial...
        `;

        const formData = new FormData(form);

        try {
            const response = await fetch('/api/reports/submit', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                form.reset();
                if (anonCheckbox) anonCheckbox.checked = false;
                if (personalFields) {
                    personalFields.style.opacity = '1';
                    personalFields.querySelectorAll('input').forEach(inp => inp.disabled = false);
                }

                // Mostrar modal de confirmación con radicado y enlace mailto
                showReportSuccessModal(data);
            } else {
                alert('Error al radicar: ' + (data.error || 'Ocurrió un problema desconocido.'));
            }
        } catch (error) {
            console.error('Error al enviar formulario:', error);
            alert('Hubo un error de conexión con el servidor local.');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnHtml;
        }
    });
}

function showReportSuccessModal(data) {
    const modal = document.getElementById('report-success-modal');
    if (!modal) return;

    const ticketCodeEl = document.getElementById('modal-ticket-code');
    if (ticketCodeEl) ticketCodeEl.textContent = data.code;

    // Configurar botón para enviar por Gmail Web
    const gmailBtn = document.getElementById('btn-send-gmail-direct');
    if (gmailBtn && data.gmail_web_url) {
        gmailBtn.href = data.gmail_web_url;
    }

    // Configurar botón para enviar por cliente de correo local
    const mailtoBtn = document.getElementById('btn-send-email-direct');
    if (mailtoBtn) {
        const mailtoUrl = data.mailto_url || `mailto:${encodeURIComponent(data.official_email)}?subject=${encodeURIComponent(data.mail_subject)}&body=${encodeURIComponent(data.mail_body)}`;
        mailtoBtn.href = mailtoUrl;
    }

    modal.classList.remove('hidden');
    modal.classList.add('flex');

    if (window.lucide) {
        lucide.createIcons();
    }
}

function closeReportSuccessModal() {
    const modal = document.getElementById('report-success-modal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}

// -------------------------------------------------------------
// 4. CONSULTA / RASTREADOR DE RADICADOS
// -------------------------------------------------------------
function initLookupModal() {
    const openBtn = document.getElementById('btn-open-lookup-modal');
    const modal = document.getElementById('filing-lookup-modal');
    const closeBtn = document.getElementById('btn-close-lookup-modal');
    const searchBtn = document.getElementById('btn-search-radicado');
    const codeInput = document.getElementById('input-lookup-code');
    const resultBox = document.getElementById('lookup-result-box');
    const emptyBox = document.getElementById('lookup-empty-state');
    const errorBox = document.getElementById('lookup-error-msg');
    const quickTrackInput = document.getElementById('quick-track-code');

    if (!modal) return;

    function openModal() {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        if (codeInput) {
            codeInput.focus();
        }
    }

    function closeModal() {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
        if (errorBox) errorBox.classList.add('hidden');
    }

    if (openBtn) openBtn.addEventListener('click', openModal);
    if (closeBtn) closeBtn.addEventListener('click', closeModal);

    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });

    async function performLookup() {
        const code = codeInput ? codeInput.value.trim() : '';
        if (!code) {
            if (errorBox) {
                errorBox.textContent = 'Por favor ingresa un código de radicado válido (ej. RAD-2026-0184).';
                errorBox.classList.remove('hidden');
            } else {
                alert('Por favor ingresa un código de radicado válido.');
            }
            if (resultBox) resultBox.classList.add('hidden');
            if (emptyBox) emptyBox.classList.remove('hidden');
            return;
        }

        if (searchBtn) {
            searchBtn.disabled = true;
            searchBtn.textContent = 'Buscando...';
        }
        if (errorBox) errorBox.classList.add('hidden');

        try {
            const res = await fetch(`/api/reports/lookup/${encodeURIComponent(code)}`);
            const data = await res.json();

            if (data.success && data.report) {
                const rep = data.report;
                if (emptyBox) emptyBox.classList.add('hidden');
                if (resultBox) {
                    resultBox.classList.remove('hidden');
                    document.getElementById('res-code').textContent = rep.code;
                    document.getElementById('res-date').textContent = rep.created_at || 'Reciente';
                    document.getElementById('res-category').textContent = rep.category;
                    document.getElementById('res-location').textContent = rep.location;
                    document.getElementById('res-subject').textContent = rep.subject;
                    document.getElementById('res-desc').textContent = rep.description;
                    document.getElementById('res-status').textContent = rep.status;
                    document.getElementById('res-notes').textContent = rep.admin_notes || 'En proceso de verificación.';
                }
            } else {
                if (resultBox) resultBox.classList.add('hidden');
                if (emptyBox) emptyBox.classList.add('hidden');
                if (errorBox) {
                    errorBox.textContent = data.error || 'No se encontró ningún radicado con este código. Verifica los caracteres.';
                    errorBox.classList.remove('hidden');
                }
            }
        } catch (err) {
            console.error('Error al consultar radicado:', err);
            if (errorBox) {
                errorBox.textContent = 'Error al conectar con la base de datos local.';
                errorBox.classList.remove('hidden');
            }
        } finally {
            if (searchBtn) {
                searchBtn.disabled = false;
                searchBtn.textContent = 'Consultar Estado';
            }
        }
    }

    if (searchBtn) searchBtn.addEventListener('click', performLookup);
    if (codeInput) {
        codeInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') performLookup();
        });
    }

    // Atajo desde el input rápido de la columna derecha
    if (quickTrackInput) {
        quickTrackInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                window.quickLookup();
            }
        });
    }

    window.quickLookup = function() {
        const val = quickTrackInput ? quickTrackInput.value.trim() : '';
        openModal();
        if (val) {
            if (codeInput) codeInput.value = val;
            setTimeout(() => {
                performLookup();
            }, 100);
        } else {
            if (codeInput) codeInput.focus();
        }
    };
}

// -------------------------------------------------------------
// 5. ACCESO ADMINISTRATIVO OCULTO (Candado en footer y Ctrl+Shift+A)
// -------------------------------------------------------------
function initAdminLoginModal() {
    const triggerBtn = document.getElementById('btn-admin-secret-lock');
    const modal = document.getElementById('admin-login-modal');
    const closeBtn = document.getElementById('btn-close-admin-login');
    const form = document.getElementById('admin-login-form');
    const errorMsg = document.getElementById('admin-login-error');

    if (!modal) return;

    function openModal() {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        const passInp = document.getElementById('admin-pass-input');
        if (passInp) {
            passInp.value = '';
            passInp.focus();
        }
        if (errorMsg) errorMsg.classList.add('hidden');
    }

    function closeModal() {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }

    if (triggerBtn) {
        triggerBtn.addEventListener('click', (e) => {
            e.preventDefault();
            openModal();
        });
    }

    if (closeBtn) closeBtn.addEventListener('click', closeModal);

    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });

    // Atajo de teclado discreto: Ctrl + Shift + A
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.shiftKey && (e.key === 'A' || e.key === 'a')) {
            e.preventDefault();
            openModal();
        }
    });

    // Detectar hash #acceso-admin
    if (window.location.hash === '#acceso-admin') {
        openModal();
    }

    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const passInput = document.getElementById('admin-pass-input');
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalBtnHtml = submitBtn.innerHTML;
            const password = passInput.value;

            submitBtn.disabled = true;
            submitBtn.textContent = 'Verificando...';

            try {
                const res = await fetch('/api/admin/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ password })
                });

                const data = await res.json();
                if (data.success) {
                    window.location.href = '/admin';
                } else {
                    if (errorMsg) {
                        errorMsg.textContent = data.error || 'Contraseña incorrecta.';
                        errorMsg.classList.remove('hidden');
                    }
                    passInput.focus();
                }
            } catch (err) {
                console.error('Error de autenticación:', err);
                if (errorMsg) {
                    errorMsg.textContent = 'Error de conexión con el servidor.';
                    errorMsg.classList.remove('hidden');
                }
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnHtml;
            }
        });
    }
}

// -------------------------------------------------------------
// 6. MODALES DE PLANTILLAS Y DERECHOS DE PETICIÓN
// -------------------------------------------------------------
function initTemplateModal() {
    const modal = document.getElementById('template-legal-modal');
    const closeBtn = document.getElementById('btn-close-template-modal');
    const copyBtn = document.getElementById('btn-copy-template-text');
    const textHolder = document.getElementById('template-text-content');
    const titleHolder = document.getElementById('template-title');

    if (!modal) return;

    function closeModal() {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }

    if (closeBtn) closeBtn.addEventListener('click', closeModal);

    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });

    document.querySelectorAll('[data-open-template]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const type = btn.dataset.openTemplate;
            loadTemplate(type);
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        });
    });

    function loadTemplate(type) {
        const contactEmailEl = document.getElementById('header-contact-email');
        const contactEmail = contactEmailEl ? contactEmailEl.textContent.trim() : 'veduriaciudadanatransparente@gmail.com';

        if (type === 'derecho-peticion') {
            titleHolder.textContent = 'Modelo de Derecho de Petición - Información Contractual (Ley 1755 / Ley 1712)';
            textHolder.value = `CIUDAD Y FECHA: Cicuco, Bolívar, [Fecha Actual]

SEÑORES: 
ALCALDÍA MUNICIPAL DE CICUCO / SECRETARÍA DE PLANEACIÓN Y OBRAS PÚBLICAS
Despacho del Ordenador del Gasto y Supervisión Contractual
Cicuco, Bolívar

REF: DERECHO DE PETICIÓN EN INTERÉS GENERAL Y DE CONTROL SOCIAL
Fundamento Legal: Artículos 20, 23, 74 y 270 de la Constitución Política; Ley 850 de 2003 (Art. 15); Ley 1712 de 2014 (Principio de Máxima Publicidad); y Ley 1755 de 2015.

Yo, [Nombre del Veedor o Ciudadano Solicitante], identificado(a) con Cédula de Ciudadanía No. [Número de Cédula], en calidad de veedor(a) ciudadano(a) / habitante del Municipio de Cicuco, acudo respetuosamente ante su despacho con el fin de formular la siguiente solicitud de copias y de información pública contractual:

1. Copia digital íntegra del Contrato No. [Indicar Número de Contrato / Objeto], suscrito entre el Municipio y [Nombre del Contratista].
2. Copia de los estudios previos, matriz de riesgos, pliego de condiciones definitivo y acta de inicio de ejecución de obra.
3. Copia de las actas de avance físico y financiero suscritas a la fecha por el contratista y la interventoría técnica externa.
4. Relación detallada de los desembolsos, órdenes de pago, comprobantes de egreso y amortización de anticipos girados al contratista.
5. Copia de las pólizas de cumplimiento, estabilidad de obra y salarios vigentes con sus respectivas certificaciones de suficiencia.

MANIFESTACIÓN DE BLINDAJE LEGAL:
Se recuerda que conforme a la jurisprudencia unificada de la Honorable Corte Constitucional (Sentencias C-292 de 2003 y T-263 de 2010), el acceso a la contratación estatal no admite reserva alguna frente a la ciudadanía fiscalizadora. El incumplimiento del término legal de 10 a 15 días hábiles (Ley 1755 de 2015) constituye falta disciplinaria sancionable por la Procuraduría General de la Nación.

NOTIFICACIONES:
Correo electrónico: ${contactEmail} / [Su Correo]
Dirección / Celular: [Su Teléfono]

Atentamente,

__________________________________________
[Firma del Solicitante / Veedor Ciudadano]
C.C. [Número de Cédula]`;
        } else if (type === 'alerta-temprana') {
            titleHolder.textContent = 'Formato de Alerta Temprana Comunitaria de Obra (Ley 850 de 2003, Art. 15)';
            textHolder.value = `DOCUMENTO DE ALERTA TEMPRANA Y CONTROL PREVENTIVO COMUNITARIO
Radicación ante: Personería Municipal de Cicuco / Contraloría Departamental / Alcaldía

FECHA: Cicuco, Bolívar, [Fecha]
PARA: Personero(a) Municipal y Supervisor Técnico Municipal
DE: Veeduría Ciudadana Cicuco Transparente
ASUNTO: Alerta Temprana por Riesgo de Paralización / Retraso Injustificado en Obra Pública

1. IDENTIFICACIÓN DEL PROYECTO:
- Nombre de la obra / contrato: [Indicar nombre del contrato u obra]
- Contratista ejecutor: [Nombre del contratista]
- Valor asignado: $[Monto] COP

2. HECHOS Y OBSERVACIONES DE CAMPO:
En visita de inspección ocular realizada el día [Fecha de inspección], el comité veedor constató las siguientes novedades:
- [Describir novedad: ej. Ausencia de maquinaria pesada, desfase de cronograma de más de 20 días, personal suspendido o falta de materiales].

3. FUNDAMENTO LEGAL:
Actuamos conforme a las facultades expresas otorgadas por el Artículo 15 de la Ley 850 de 2003, en concordancia con el principio de eficacia de la función pública (Art. 209 C.P.).

4. SOLICITUD PREVENTIVA:
Solicitamos a la administración municipal ordenar de inmediato visita pericial conjunta con el comité veedor y requerir a la aseguradora y al contratista el plan de contingencia para evitar detrimento patrimonial.

Comité Veedor de Obras e Infraestructura
Veeduría Ciudadana Cicuco Transparente
Correo: ${contactEmail}`;
        } else if (type === 'respuesta-blindaje') {
            titleHolder.textContent = 'Minuta de Blindaje y Respuesta ante Advertencias o Amenazas de Demanda';
            textHolder.value = `DOCUMENTO DE RECHAZO A CENSURA Y RATIFICACIÓN DE BLINDAJE JURÍDICO
(Para responder a contratistas o funcionarios que pretendan intimidar con denuncias por injuria o calumnia)

CIUDAD Y FECHA: Cicuco, Bolívar, [Fecha]
DESTINATARIO: [Nombre del funcionario o contratista requirente]

REF: RESPUESTA A SOLICITUD DE RECTIFICACIÓN / MANIFESTACIÓN DE AMPARO CONSTITUCIONAL
Marco Normativo: Artículos 20 y 270 de la Constitución Política; Sentencias C-292 de 2003, T-263 de 2010 y T-063 de 2017 de la Corte Constitucional de Colombia.

Me dirijo a usted en respuesta a su comunicación, en la cual manifiesta inconformidad por las alertas y fiscalizaciones ciudadanas publicadas por esta Veeduría en relación con los recursos públicos invertidos en el Municipio de Cicuco:

1. NATURALEZA DE LA INFORMACIÓN:
Las alertas emitidas por la Veeduría Ciudadana Cicuco Transparente no obedecen a juicios personales ni imputaciones deshonrosas individuales, sino a la confrontación objetiva entre los cronogramas contractuales oficiales (publicados en el SECOP) y las verificaciones visuales sobre el terreno.

2. BLINDAJE JURISPRUDENCIAL Y AUSENCIA DE CALUMNIA:
La Corte Constitucional en reiterada jurisprudencia (Sentencias T-263 de 2010 y T-063 de 2017) ha determinado de manera tajante:
a) Los funcionarios públicos y contratistas del Estado están sometidos a un nivel superior de escrutinio, crítica e inspección pública que los ciudadanos del común.
b) El ejercicio legítimo de control social amparado en la Ley 850 de 2003 goza de presunción de buena fe constitucional. No existe delito de calumnia ni injuria cuando el veedor traslada inquietudes públicas sustentadas en indicios fácticos.
c) La instrumentalización de advertencias penales o demandas temerarias (pleitos tipo SLAPP) constituye una práctica ilícita de censura y acoso judicial que viola el Artículo 20 de la Carta Política.

3. CONCLUSIÓN:
Reafirmamos nuestro compromiso ineludible con la transparencia del erario público de Cicuco y mantenemos abiertos los canales institucionales para que la entidad acredite documentalmente las subsanaciones de las falencias advertidas.

Atentamente,

Comité Directivo y Jurídico
Veeduría Ciudadana Cicuco Transparente
Correo Oficial: ${contactEmail}`;
        }
    }

    if (copyBtn && textHolder) {
        copyBtn.addEventListener('click', async () => {
            try {
                await copyTextToClipboard(textHolder.value);
                const originalHtml = copyBtn.innerHTML;
                copyBtn.innerHTML = `
                    <svg class="w-4 h-4 text-emerald-400 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
                    ¡Texto Copiado!
                `;
                setTimeout(() => {
                    copyBtn.innerHTML = originalHtml;
                }, 2500);
            } catch (err) {
                textHolder.select();
                document.execCommand('copy');
                alert('Texto seleccionado y copiado.');
            }
        });
    }
}

// -------------------------------------------------------------
// 7. MODAL DETALLES DE CONTRATO
// -------------------------------------------------------------
function initContractDetailsModal() {
    const modal = document.getElementById('contract-detail-modal');
    const closeBtn = document.getElementById('btn-close-contract-modal');

    if (!modal) return;

    function closeModal() {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }

    if (closeBtn) closeBtn.addEventListener('click', closeModal);

    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });

    document.querySelectorAll('[data-view-contract]').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const id = btn.dataset.viewContract;
            try {
                const res = await fetch(`/api/contracts/${id}`);
                if (!res.ok) {
                    alert('No se pudo cargar la información del contrato.');
                    return;
                }
                const contract = await res.json();
                if (contract && !contract.error) {
                    populateContractModal(contract);
                    modal.classList.remove('hidden');
                    modal.classList.add('flex');
                    if (window.lucide) lucide.createIcons();
                } else {
                    alert(contract.error || 'Contrato no encontrado.');
                }
            } catch (err) {
                console.error('Error al cargar contrato:', err);
                alert('Error al consultar los datos del contrato.');
            }
        });
    });

    function populateContractModal(c) {
        document.getElementById('cmodal-code').textContent = c.code || '';
        document.getElementById('cmodal-title').textContent = c.title || '';
        document.getElementById('cmodal-sector').textContent = c.sector || '';
        document.getElementById('cmodal-contractor').textContent = c.contractor || '';
        document.getElementById('cmodal-entity').textContent = c.entity || '';
        let modalAmount = c.amount || '';
        if (modalAmount.startsWith('.')) {
            modalAmount = '$450' + modalAmount;
        } else if (modalAmount && !modalAmount.startsWith('$') && !modalAmount.toLowerCase().includes('auditor')) {
            modalAmount = '$' + modalAmount;
        }
        document.getElementById('cmodal-amount').textContent = modalAmount;
        document.getElementById('cmodal-inspection').textContent = c.last_inspection || 'Reciente';
        document.getElementById('cmodal-status').textContent = c.status || '';
        
        const physVal = c.progress_physical || 0;
        const finVal = c.progress_financial || 0;

        document.getElementById('cmodal-phys').textContent = physVal + '%';
        document.getElementById('cmodal-phys-bar').style.width = Math.min(physVal, 100) + '%';
        document.getElementById('cmodal-fin').textContent = finVal + '%';
        document.getElementById('cmodal-fin-bar').style.width = Math.min(finVal, 100) + '%';
        document.getElementById('cmodal-summary').textContent = c.summary || 'Sin resumen registrado.';

        const docBtn = document.getElementById('cmodal-doc-btn');
        if (c.file_path) {
            docBtn.href = `/uploads/${c.file_path}`;
            docBtn.target = '_blank';
            docBtn.classList.remove('hidden');
        } else {
            docBtn.classList.add('hidden');
        }

        const secopBtn = document.getElementById('cmodal-secop-btn');
        if (c.external_link) {
            secopBtn.href = c.external_link;
            secopBtn.target = '_blank';
            secopBtn.classList.remove('hidden');
        } else {
            secopBtn.classList.add('hidden');
        }
    }
}

// -------------------------------------------------------------
// 8. TECLA ESCAPE GLOBAL PARA CERRAR CUALQUIER MODAL
// -------------------------------------------------------------
function initGlobalEscapeKey() {
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const openModals = [
                document.getElementById('contract-detail-modal'),
                document.getElementById('template-legal-modal'),
                document.getElementById('filing-lookup-modal'),
                document.getElementById('admin-login-modal'),
                document.getElementById('report-success-modal')
            ];
            openModals.forEach(modal => {
                if (modal && !modal.classList.contains('hidden')) {
                    modal.classList.add('hidden');
                    modal.classList.remove('flex');
                }
            });
        }
    });
}

// -------------------------------------------------------------
// 9. COPIAR CORREO OFICIAL DINÁMICAMENTE AL PORTAPAPELES
// -------------------------------------------------------------
window.copyOfficialEmail = function() {
    const emailEl = document.getElementById('header-contact-email') || document.querySelector('[data-official-email]');
    const email = emailEl ? (emailEl.dataset.officialEmail || emailEl.textContent.trim()) : 'veduriaciudadanatransparente@gmail.com';

    copyTextToClipboard(email).then(() => {
        const toast = document.getElementById('global-toast');
        if (toast) {
            toast.textContent = `¡Correo ${email} copiado al portapapeles!`;
            toast.classList.remove('hidden');
            setTimeout(() => {
                toast.classList.add('hidden');
            }, 3000);
        } else {
            alert(`Correo copiado: ${email}`);
        }
    }).catch(err => {
        alert(`Correo oficial de denuncias: ${email}`);
    });
};
