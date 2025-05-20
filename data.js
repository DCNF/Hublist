function readXMLHublist(link) {
    fetch(link)
        .then(response => response.ok ? response.text() : Promise.reject('Network response was not ok'))
        .then(data => {
            const parser = new DOMParser();
            const xmlDoc = parser.parseFromString(data, "application/xml");
            tableFromXML(xmlDoc.getElementsByTagName("Hub"));
        })
        .catch(error => console.error('There has been a problem with your fetch operation:', error));
}

function tableFromXML(data) {
    const tableTemplate = `
        <table class="table table-responsive table-striped" id="sortableTable" style="width:100%">
            <thead>
                <tr>
                    <th scope="col">Name</th>
                    <th scope="col">Address</th>
                    <th scope="col">Encoding</th>
                    <th scope="col">Shared</th>
                    <th scope="col">Users</th>
                    <th scope="col">More details</th>
                </tr>
            </thead>
            <tbody>
                ${Array.from(data).map(hub => `
                    <tr>
                        <td title="${he.encode(hub.getAttribute('Description'))}" class="${hub.getAttribute('Status')}" data-order="${he.encode(hub.getAttribute('Name'))}">
                            ${he.encode(hub.getAttribute('Name'))}
                        </td>
                        <td>
                            <a href="${hub.getAttribute('Address')}">${hub.getAttribute('Address')}</a>
                        </td>
                        <td>${hub.getAttribute('Encoding')}</td>
                        <td data-order="${hub.getAttribute('Shared')}">${humanFileSize(hub.getAttribute('Shared'), true)}</td>
                        <td>${hub.getAttribute('Users')}</td>
                        <td>
                            <button type="button" class="btn btn-link" data-toggle="modal" data-target="#hubModal" onclick='showHubModal(${JSON.stringify({
                                name: he.encode(hub.getAttribute('Name')),
                                address: hub.getAttribute('Address'),
                                description: he.encode(hub.getAttribute('Description')),
                                users: hub.getAttribute('Users'),
                                country: hub.getAttribute('Country'),
                                shared: humanFileSize(hub.getAttribute('Shared'), true),
                                minshare: humanFileSize(hub.getAttribute('Minshare'), true),
                                minslots: hub.getAttribute('Minslots'),
                                maxhubs: hub.getAttribute('Maxhubs'),
                                maxusers: hub.getAttribute('Maxusers'),
                                reliability: hub.getAttribute('Reliability'),
                                rating: hub.getAttribute('Rating'),
                                encoding: hub.getAttribute('Encoding'),
                                software: hub.getAttribute('Software'),
                                website: hub.getAttribute('Website'),
                                email: hub.getAttribute('Email'),
                                asn: hub.getAttribute('ASN'),
                                operators: hub.getAttribute('Operators'),
                                bots: hub.getAttribute('Bots'),
                                infected: hub.getAttribute('Infected'),
                                status: hub.getAttribute('Status'),
                                failover: hub.getAttribute('Failover')
                            })})'>
                                Hub details
                            </button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;

    document.getElementById("HublistTable").innerHTML = tableTemplate;

    $(document).ready(function() {
        $('#sortableTable').DataTable({
            pageLength: 25,
            lengthMenu: [[10, 25, 50, 100, 250, -1], [10, 25, 50, 100, 250, "All"]],
            columnDefs: [
                { searchable: false, targets: [3, 4] },
                { orderable: false, targets: 1 },
                { width: "40%", targets: [0, 1] }
            ],
            order: [],
            rowReorder: { selector: 'td:nth-child(2)' },
            responsive: true
        });
    });
}

function showHubModal(hubData) {
    document.getElementById("hubModalName").innerHTML = `Hub: ${hubData.name}`;
    document.getElementById("hubname").innerHTML = hubData.name;
    document.getElementById("hubaddress").innerText = hubData.address;
    document.getElementById("hubdescription").innerHTML = hubData.description;
    document.getElementById("hubusers").innerText = hubData.users;
    document.getElementById("hubcountry").innerText = hubData.country;
    document.getElementById("hubshared").innerText = hubData.shared;
    document.getElementById("hubminshare").innerText = hubData.minshare;
    document.getElementById("hubminslots").innerText = hubData.minslots;
    document.getElementById("hubmaxhubs").innerText = hubData.maxhubs;
    document.getElementById("hubmaxusers").innerText = hubData.maxusers;
    document.getElementById("hubreliability").innerText = `${hubData.reliability}%`;
    document.getElementById("hubrating").innerText = hubData.rating;
    document.getElementById("hubencoding").innerText = hubData.encoding;
    document.getElementById("hubsoftware").innerText = hubData.software;
    document.getElementById("hubwebsite").innerText = hubData.website;
    document.getElementById("hubemail").innerText = hubData.email;
    document.getElementById("hubasn").innerText = hubData.asn;
    document.getElementById("huboperators").innerText = hubData.operators;
    document.getElementById("hubbots").innerText = hubData.bots;
    document.getElementById("hubinfected").innerText = hubData.infected;
    document.getElementById("hubstatus").innerHTML = `<span title="${hubData.status}">${hubData.status === "Online" ? "&#10004;" : "&#10060;"}</span>`;
    document.getElementById("hubfailover").innerText = hubData.failover;
}

// based on https://stackoverflow.com/a/14919494
function humanFileSize(bytes, si) {
    const thresh = si ? 1000 : 1024;
    if (Math.abs(bytes) < thresh) return `${bytes} B`;
    const units = si
        ? ['kB','MB','GB','TB','PB','EB','ZB','YB']
        : ['KiB','MiB','GiB','TiB','PiB','EiB','ZiB','YiB'];
    let u = -1;
    do {
        bytes /= thresh;
        ++u;
    } while(Math.abs(bytes) >= thresh && u < units.length - 1);
    return `${bytes.toFixed(1)} ${units[u]}`;
}
