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
	
	for (var i = data.length - 1; i >= 0; i--) {
		tab += '<tr>';
		tab += '<td title="' + he.encode(data[i].getAttribute('Description')) + '" class="' + data[i].getAttribute('Status') + '" data-order="' + he.encode(data[i].getAttribute('Name')) + '" >';
		tab += '' + he.encode(data[i].getAttribute('Name')) + '' + '</td>';
		tab += '<td><a href="' + data[i].getAttribute('Address') + '" >' + data[i].getAttribute('Address') + '</a></td>';
		tab += '<td>' + data[i].getAttribute('Encoding') + '</td>';
		tab += '<td data-order="' + data[i].getAttribute('Shared') + '">' + humanFileSize(data[i].getAttribute('Shared'), true) + '</td>';
		tab += '<td>' + data[i].getAttribute('Users') + '</td>';
		tab += '<td><button type="button" class="btn btn-link" data-toggle="modal" data-target="#hubModal" onclick="buildModal(\'' 
		+ he.encode(data[i].getAttribute('Name')) 
		+ '\',\'' + data[i].getAttribute('Address')
		+ '\',\'' + encodeURIComponent(he.encode(data[i].getAttribute('Description')))
		+ '\',\'' + data[i].getAttribute('Users') 
		+ '\',\'' + data[i].getAttribute('Country') 
		+ '\',\'' + humanFileSize(data[i].getAttribute('Shared'), true) 
		+ '\',\'' + humanFileSize(data[i].getAttribute('Minshare'), true) 
		+ '\',\'' + data[i].getAttribute('Minslots') 
		+ '\',\'' + data[i].getAttribute('Maxhubs') 
		+ '\',\'' + data[i].getAttribute('Maxusers') 
		+ '\',\'' + data[i].getAttribute('Reliability') 
		+ '\',\'' + data[i].getAttribute('Rating') 
		+ '\',\'' + data[i].getAttribute('Encoding') 
		+ '\',\'' + data[i].getAttribute('Software') 
		+ '\',\'' + data[i].getAttribute('Website') 
		+ '\',\'' + data[i].getAttribute('Email') 
		+ '\',\'' + data[i].getAttribute('ASN') 
		+ '\',\'' + data[i].getAttribute('Operators') 
		+ '\',\'' + data[i].getAttribute('Bots') 
		+ '\',\'' + data[i].getAttribute('Infected') 
		+ '\',\'' + data[i].getAttribute('Status') 
		+ '\',\'' + data[i].getAttribute('Failover') 
		+ '\');">';
		tab += 'Hub details</button></td>';
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
			aaSorting: [],
			rowReorder: {
				selector: 'td:nth-child(2)'
			},
			responsive: true
		});
	});
}

function buildModal(name, address, description, users, country, shared, minshare, minslots, maxhubs, maxusers, reliability, rating, encoding, software, website, email, asn, operators, bots, infected, status, failover){
	document.getElementById("hubModalName").innerText = 'Hub: ' + name;
	document.getElementById("hubname").innerText = name;
	document.getElementById("hubaddress").innerText = address;
	document.getElementById("hubdescription").innerText = he.decode(decodeURIComponent(description));
	document.getElementById("hubusers").innerText = users;
	document.getElementById("hubcountry").innerText = country;
	document.getElementById("hubshared").innerText = shared;
	document.getElementById("hubminshare").innerText = minshare;
	document.getElementById("hubminslots").innerText = minslots;
	document.getElementById("hubmaxhubs").innerText = maxhubs;
	document.getElementById("hubmaxusers").innerText = maxusers;
	document.getElementById("hubreliability").innerText = reliability + '%';
	document.getElementById("hubrating").innerText = rating;
	document.getElementById("hubencoding").innerText = encoding;
	document.getElementById("hubsoftware").innerText = software;
	document.getElementById("hubwebsite").innerText = website;
	document.getElementById("hubemail").innerText = email;
	document.getElementById("hubasn").innerText = asn;
	document.getElementById("huboperators").innerText = operators;
	document.getElementById("hubbots").innerText = bots;
	document.getElementById("hubinfected").innerText = infected;
	document.getElementById("hubstatus").innerHTML = '<span title=' + status + '>' + (status === "Online" ? "&#9989;" : "&#10060;") + '</span>';
	document.getElementById("hubfailover").innerText = failover;
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
