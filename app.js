(function () {
    'use strict';

    const PAGE_SIZE = 25;
    const XML_URL = 'hublist.xml';

    let hubs = [];
    let hubsByAddress = new Map();
    let filteredHubs = [];
    let currentPage = 1;
    let sortKey = null;
    let sortAsc = true;

    const dom = {
        tableBody: document.getElementById('hubTableBody'),
        searchInput: document.getElementById('searchInput'),
        hubCount: document.getElementById('hubCount'),
        loading: document.getElementById('loading'),
        error: document.getElementById('error'),
        pagination: document.getElementById('pagination'),
        prevPage: document.getElementById('prevPage'),
        nextPage: document.getElementById('nextPage'),
        pageInfo: document.getElementById('pageInfo'),
        modal: document.getElementById('hubModal'),
        modalTitle: document.getElementById('modalTitle'),
        modalBody: document.getElementById('modalBody'),
        hubTable: document.getElementById('hubTable'),
    };

    function init() {
        fetchHubs();
        bindEvents();
    }

    async function fetchHubs() {
        try {
            const response = await fetch(XML_URL);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const text = await response.text();
            const parser = new DOMParser();
            const xmlDoc = parser.parseFromString(text, 'application/xml');
            const hubElements = xmlDoc.getElementsByTagName('Hub');

            hubs = Array.from(hubElements).map(parseHub);
            hubsByAddress = new Map(hubs.map(h => [h.address, h]));
            filteredHubs = [...hubs];
            sortHubs();

            dom.loading.hidden = true;
            render();
        } catch (err) {
            dom.loading.hidden = true;
            dom.error.textContent = `Failed to load hub list: ${err.message}`;
            dom.error.hidden = false;
        }
    }

    function parseHub(el) {
        return {
            name: el.getAttribute('Name') || '',
            address: el.getAttribute('Address') || '',
            description: el.getAttribute('Description') || '',
            users: parseInt(el.getAttribute('Users'), 10) || 0,
            country: el.getAttribute('Country') || '',
            shared: parseInt(el.getAttribute('Shared'), 10) || 0,
            minshare: el.getAttribute('Minshare') || '',
            minslots: el.getAttribute('Minslots') || '',
            maxhubs: el.getAttribute('Maxhubs') || '',
            maxusers: el.getAttribute('Maxusers') || '',
            reliability: el.getAttribute('Reliability') || '',
            rating: el.getAttribute('Rating') || '',
            encoding: el.getAttribute('Encoding') || '',
            software: el.getAttribute('Software') || '',
            website: el.getAttribute('Website') || '',
            email: el.getAttribute('Email') || '',
            asn: el.getAttribute('ASN') || '',
            operators: el.getAttribute('Operators') || '',
            bots: el.getAttribute('Bots') || '',
            infected: el.getAttribute('Infected') || '',
            status: el.getAttribute('Status') || '',
            failover: el.getAttribute('Failover') || '',
        };
    }

    function bindEvents() {
        dom.searchInput.addEventListener('input', debounce(onSearch, 200));
        dom.prevPage.addEventListener('click', () => goToPage(currentPage - 1));
        dom.nextPage.addEventListener('click', () => goToPage(currentPage + 1));

        dom.hubTable.querySelectorAll('th[data-sort]').forEach(th => {
            th.addEventListener('click', () => onSort(th.dataset.sort));
            th.setAttribute('tabindex', '0');
            th.addEventListener('keydown', e => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    onSort(th.dataset.sort);
                }
            });
        });

        dom.modal.addEventListener('click', e => {
            if (e.target === dom.modal) closeModal();
        });
        dom.modal.addEventListener('close', () => {
            document.documentElement.classList.remove('modal-is-open', 'modal-is-closing');
        });
    }

    function onSearch() {
        const query = dom.searchInput.value.toLowerCase().trim();
        if (!query) {
            filteredHubs = [...hubs];
        } else {
            filteredHubs = hubs.filter(h =>
                h.name.toLowerCase().includes(query) ||
                h.address.toLowerCase().includes(query) ||
                h.description.toLowerCase().includes(query) ||
                h.country.toLowerCase().includes(query) ||
                h.software.toLowerCase().includes(query) ||
                h.encoding.toLowerCase().includes(query)
            );
        }
        currentPage = 1;
        sortHubs();
        render();
    }

    function onSort(key) {
        if (sortKey === key) {
            sortAsc = !sortAsc;
        } else {
            sortKey = key;
            sortAsc = true;
        }
        sortHubs();
        render();
    }

    function sortHubs() {
        if (!sortKey) return;
        filteredHubs.sort((a, b) => {
            let va = a[sortKey];
            let vb = b[sortKey];

            if (sortKey === 'shared' || sortKey === 'users') {
                va = Number(va) || 0;
                vb = Number(vb) || 0;
                return sortAsc ? va - vb : vb - va;
            }

            va = String(va).toLowerCase();
            vb = String(vb).toLowerCase();
            if (va < vb) return sortAsc ? -1 : 1;
            if (va > vb) return sortAsc ? 1 : -1;
            return 0;
        });
    }

    function render() {
        renderTable();
        renderPagination();
        renderSortIndicators();
        renderCount();
    }

    function renderTable() {
        const start = (currentPage - 1) * PAGE_SIZE;
        const pageHubs = filteredHubs.slice(start, start + PAGE_SIZE);

        if (pageHubs.length === 0) {
            dom.tableBody.innerHTML = '<tr><td colspan="3" style="text-align:center">No hubs found</td></tr>';
            return;
        }

        dom.tableBody.innerHTML = pageHubs.map(hub => `
            <tr class="hub-row" data-address="${escapeAttr(hub.address)}" tabindex="0" aria-label="${escapeAttr(hub.name)}">
                <td>
                    <span class="status-badge ${hub.status === 'Online' ? 'status-online' : 'status-offline'}" title="${escapeAttr(hub.status)}">${hub.status === 'Online' ? '●' : '○'}</span>
                    ${escapeHtml(hub.name)}
                </td>
                <td>${humanFileSize(hub.shared)}</td>
                <td>${hub.users.toLocaleString()}</td>
            </tr>
        `).join('');

        dom.tableBody.querySelectorAll('.hub-row').forEach(row => {
            const hub = hubsByAddress.get(row.dataset.address);
            row.addEventListener('click', () => hub && openModal(hub));
            row.addEventListener('keydown', e => {
                if (e.key === 'Enter' && hub) openModal(hub);
            });
        });
    }

    function renderPagination() {
        const totalPages = Math.ceil(filteredHubs.length / PAGE_SIZE);
        if (totalPages <= 1) {
            dom.pagination.hidden = true;
            return;
        }
        dom.pagination.hidden = false;
        dom.pageInfo.textContent = `${currentPage} / ${totalPages}`;
        dom.prevPage.disabled = currentPage <= 1;
        dom.nextPage.disabled = currentPage >= totalPages;
    }

    function renderSortIndicators() {
        dom.hubTable.querySelectorAll('th[data-sort]').forEach(th => {
            const key = th.dataset.sort;
            th.classList.remove('sort-asc', 'sort-desc');
            if (key === sortKey) {
                th.classList.add(sortAsc ? 'sort-asc' : 'sort-desc');
            }
        });
    }

    function renderCount() {
        const total = hubs.length;
        const shown = filteredHubs.length;
        dom.hubCount.textContent = shown === total
            ? `${total} hubs`
            : `${shown} of ${total} hubs`;
    }

    function goToPage(page) {
        const totalPages = Math.ceil(filteredHubs.length / PAGE_SIZE);
        currentPage = Math.max(1, Math.min(page, totalPages));
        render();
        dom.hubTable.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function openModal(hub) {
        const protocol = getProtocol(hub.address);
        const isOnline = hub.status === 'Online';

        dom.modalTitle.innerHTML = `
            <strong>${escapeHtml(hub.name)}</strong>
            <small class="status-badge ${isOnline ? 'status-online' : 'status-offline'}">${isOnline ? 'Online' : 'Offline'}</small>
        `;

        dom.modalBody.innerHTML = `
            <section>
                <h6>Hub</h6>
                <dl>
                    <dt>Address</dt>
                    <dd class="address-cell">
                        <a href="${escapeAttr(hub.address)}" target="_blank" rel="noopener">${escapeHtml(hub.address)}</a>
                        <button class="outline copy-btn" onclick="copyText(this, '${escapeAttr(hub.address)}')">Copy</button>
                    </dd>
                    ${hub.description ? `<dt>Description</dt><dd>${escapeHtml(hub.description)}</dd>` : ''}
                    ${hub.country ? `<dt>Country</dt><dd>${escapeHtml(hub.country)}</dd>` : ''}
                    ${hub.website ? `<dt>Website</dt><dd><a href="${escapeAttr(hub.website)}" target="_blank" rel="noopener">${escapeHtml(hub.website)}</a></dd>` : ''}
                    ${hub.email ? `<dt>Email</dt><dd><a href="mailto:${escapeAttr(hub.email)}">${escapeHtml(hub.email)}</a></dd>` : ''}
                </dl>
            </section>
            <section>
                <h6>Network</h6>
                <dl>
                    <dt>Users</dt><dd>${hub.users.toLocaleString()}</dd>
                    ${hub.operators ? `<dt>Operators</dt><dd>${hub.operators}</dd>` : ''}
                    ${hub.bots ? `<dt>Bots</dt><dd>${hub.bots}</dd>` : ''}
                    ${hub.infected ? `<dt>Infected</dt><dd>${hub.infected}</dd>` : ''}
                </dl>
            </section>
            <section>
                <h6>Sharing</h6>
                <dl>
                    <dt>Shared</dt><dd>${humanFileSize(hub.shared)}</dd>
                    ${hub.minshare ? `<dt>Min share</dt><dd>${humanFileSize(parseInt(hub.minshare, 10) || 0)}</dd>` : ''}
                    ${hub.minslots ? `<dt>Min slots</dt><dd>${hub.minslots}</dd>` : ''}
                </dl>
            </section>
            <section>
                <h6>Limits</h6>
                <dl>
                    ${hub.maxhubs ? `<dt>Max hubs</dt><dd>${hub.maxhubs}</dd>` : ''}
                    ${hub.maxusers ? `<dt>Max users</dt><dd>${hub.maxusers}</dd>` : ''}
                    ${hub.reliability ? `<dt>Reliability</dt><dd>${hub.reliability}%</dd>` : ''}
                    ${hub.rating ? `<dt>Rating</dt><dd>${hub.rating}</dd>` : ''}
                </dl>
            </section>
            <section>
                <h6>Technical</h6>
                <dl>
                    <dt>Protocol</dt><dd>${escapeHtml(protocol)}</dd>
                    <dt>Encoding</dt><dd>${escapeHtml(hub.encoding)}</dd>
                    ${hub.software ? `<dt>Software</dt><dd>${escapeHtml(hub.software)}</dd>` : ''}
                    ${hub.asn ? `<dt>ASN</dt><dd>${escapeHtml(hub.asn)}</dd>` : ''}
                    ${hub.failover ? `<dt>Failover</dt><dd><a href="${escapeAttr(hub.failover)}" target="_blank" rel="noopener">${escapeHtml(hub.failover)}</a></dd>` : ''}
                </dl>
            </section>
        `;

        dom.modal.showModal();
        document.documentElement.classList.add('modal-is-open', 'modal-is-opening');
        setTimeout(() => document.documentElement.classList.remove('modal-is-opening'), 250);
    }

    function closeModal() {
        if (!dom.modal.open) return;
        document.documentElement.classList.add('modal-is-closing');
        setTimeout(() => {
            dom.modal.close();
            document.documentElement.classList.remove('modal-is-open', 'modal-is-closing');
        }, 250);
    }

    function getProtocol(address) {
        const scheme = address.split('://')[0]?.toLowerCase() || '';
        const map = {
            'adcs': 'ADCS', 'adc': 'ADC',
            'dchubs': 'DCHUBS', 'dchub': 'DCHUB',
            'nmdcs': 'NMDCS', 'nmdc': 'NMDC',
        };
        return map[scheme] || scheme.toUpperCase();
    }

    function humanFileSize(bytes) {
        if (!bytes || bytes === 0) return '0 B';
        const thresh = 1000;
        const units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
        let u = 0;
        let size = Math.abs(bytes);
        while (size >= thresh && u < units.length - 1) {
            size /= thresh;
            ++u;
        }
        return `${size.toFixed(u === 0 ? 0 : 1)} ${units[u]}`;
    }

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function escapeAttr(str) {
        return str.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    function debounce(fn, delay) {
        let timer;
        return function (...args) {
            clearTimeout(timer);
            timer = setTimeout(() => fn.apply(this, args), delay);
        };
    }

    window.closeModal = closeModal;

    window.copyText = async function (btn, text) {
        try {
            await navigator.clipboard.writeText(text);
        } catch {
            const input = document.createElement('input');
            input.value = text;
            document.body.appendChild(input);
            input.select();
            document.execCommand('copy');
            document.body.removeChild(input);
        }
        btn.textContent = 'Copied!';
        setTimeout(() => { btn.textContent = 'Copy'; }, 2000);
    };

    init();
})();
