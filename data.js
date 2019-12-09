function readXMLHublist(link) {
	var req = new XMLHttpRequest();
	req.open('GET', link, true); // true for asynchronous

	req.onreadystatechange = function () {
		if (req.readyState == 4) { // 4 == XMLHttpRequest.DONE ie8+
			if((req.status == 200) || (req.status == 304)) {
				console.log('OK');
				var objXML = new DOMParser().parseFromString(req.responseText, "application/xml");
				tableFromXML(objXML.getElementsByTagName("Hub"));
			}
			else {
				console.log('ERROR');
			}
		}
	};
	req.send(null);
}

function tableFromXML(data) {
	var tab = '<table class="table table-responsive table-striped" id="sortableTable" style="width:100%">';
	tab += '<thead>';
	tab += '<tr>';
	tab += '<th scope="col">Name</th>';
	tab += '<th scope="col">Address</th>';
	tab += '<th scope="col">Encoding</th>';
	tab += '<th scope="col">Shared</th>';
	tab += '<th scope="col">Users</th>';
	tab += '<th scope="col">More details</th>';
	tab += '</tr>';
	tab += '</thead>';
	tab += '</tbody>';

	for (var i = 0; i < data.length; i++) {
		tab += '<tr>';
		tab += '<td title="' + he.encode(data[i].getAttribute('Description')) + '" class="' + data[i].getAttribute('Status') + '" data-order="' + he.encode(data[i].getAttribute('Name')) + '" >';
		tab += '' + he.encode(data[i].getAttribute('Name')) + '' + '</td>';
		tab += '<td><a href="' + data[i].getAttribute('Address') + '" >' + data[i].getAttribute('Address') + '</a></td>';
		tab += '<td>' + data[i].getAttribute('Encoding') + '</td>';
		tab += '<td data-order="' + data[i].getAttribute('Shared') + '">' + humanFileSize(data[i].getAttribute('Shared'), true) + '</td>';
		tab += '<td>' + data[i].getAttribute('Users') + '</td>';
		tab += '<td><button type="button" class="btn btn-link" data-toggle="modal" data-target="#hubModal" '
		tab += 'data-name="' + encodeURIComponent(he.encode(data[i].getAttribute('Name'))) + '" '
		tab += 'data-address="' + data[i].getAttribute('Address') + '" '
		tab += 'data-description="' + encodeURIComponent(he.encode(data[i].getAttribute('Description'))) + '" '
		tab += 'data-users="' + data[i].getAttribute('Users') + '" '
		tab += 'data-country="' + data[i].getAttribute('Country') + '" '
		tab += 'data-shared="' + humanFileSize(data[i].getAttribute('Shared'), true) + '" '
		tab += 'data-minshare="' + humanFileSize(data[i].getAttribute('Minshare'), true) + '" '
		tab += 'data-minslots="' + data[i].getAttribute('Minslots') + '" '
		tab += 'data-maxhubs="' + data[i].getAttribute('Maxhubs') + '" '
		tab += 'data-maxusers="' + data[i].getAttribute('Maxusers') + '" '
		tab += 'data-reliability="' + data[i].getAttribute('Reliability') + '" '
		tab += 'data-rating="' + data[i].getAttribute('Rating') + '" '
		tab += 'data-encoding="' + data[i].getAttribute('Encoding') + '" '
		tab += 'data-software="' + data[i].getAttribute('Software') + '" '
		tab += 'data-website="' + data[i].getAttribute('Website') + '" '
		tab += 'data-email="' + data[i].getAttribute('Email') + '" '
		tab += 'data-asn="' + data[i].getAttribute('ASN') + '" '
		tab += 'data-operators="' + data[i].getAttribute('Operators') + '" '
		tab += 'data-bots="' + data[i].getAttribute('Bots') + '" '
		tab += 'data-infected="' + data[i].getAttribute('Infected') + '" '
		tab += 'data-status="' + data[i].getAttribute('Status') + '" '
		tab += 'data-failover="' + data[i].getAttribute('Failover') + '" '
		tab += '>Hub details</button></td>';
		tab += '</tr>';
	}

	tab += '</tbody>';
	tab += '</table>';

	document.getElementById("HublistTable").innerHTML = tab;

	$(document).ready(function() {
		$('#sortableTable').DataTable({
			"pageLength": 25,
			"lengthMenu": [[10, 25, 50, 100, 250, -1], [10, 25, 50, 100, 250, "All"]],
			"columnDefs": [
				{ "searchable": false, "targets": [3, 4] },
				{ "orderable": false, "targets": 1 },
				{ "width": "40%", "targets": [0, 1] }
			],
			"order": [],
			rowReorder: {
				selector: 'td:nth-child(2)'
			},
			responsive: true
		});
		$("#hubModal").on('show.bs.modal', function (event) {
			var button = $(event.relatedTarget);
			document.getElementById("hubModalName").innerHTML = 'Hub: ' + decodeURIComponent(button.data('name'));
			document.getElementById("hubname").innerHTML = decodeURIComponent(button.data('name'));
			document.getElementById("hubaddress").innerText = button.data('address');
			document.getElementById("hubdescription").innerHTML = decodeURIComponent(button.data('description'));
			document.getElementById("hubusers").innerText = button.data('users');
			document.getElementById("hubcountry").innerText = button.data('country');
			document.getElementById("hubshared").innerText = button.data('shared');
			document.getElementById("hubminshare").innerText = button.data('minshare');
			document.getElementById("hubminslots").innerText = button.data('minslots');
			document.getElementById("hubmaxhubs").innerText = button.data('maxhubs');
			document.getElementById("hubmaxusers").innerText = button.data('maxusers');
			document.getElementById("hubreliability").innerText = button.data('reliability') + '%';
			document.getElementById("hubrating").innerText = button.data('rating');
			document.getElementById("hubencoding").innerText = button.data('encoding');
			document.getElementById("hubsoftware").innerText = button.data('software');
			document.getElementById("hubwebsite").innerText = button.data('website');
			document.getElementById("hubemail").innerText = button.data('email');
			document.getElementById("hubasn").innerText = button.data('asn');
			document.getElementById("huboperators").innerText = button.data('operators');
			document.getElementById("hubbots").innerText = button.data('bots');
			document.getElementById("hubinfected").innerText = button.data('infected');
			document.getElementById("hubstatus").innerHTML = '<span title=' + button.data('status') + '>' + (button.data('status') === "Online" ? "&#10004;" : "&#10060;") + '</span>';
			document.getElementById("hubfailover").innerText = button.data('failover');
		});
	});
}

// based on https://stackoverflow.com/a/14919494
function humanFileSize(bytes, si) {
	var thresh = si ? 1000 : 1024;
	if(Math.abs(bytes) < thresh) {
		return bytes + ' B';
	}
	var units = si
		? ['kB','MB','GB','TB','PB','EB','ZB','YB']
		: ['KiB','MiB','GiB','TiB','PiB','EiB','ZiB','YiB'];
	var u = -1;
	do {
		bytes /= thresh;
		++u;
	} while(Math.abs(bytes) >= thresh && u < units.length - 1);
	return bytes.toFixed(1)+' '+units[u];
}
