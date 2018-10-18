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
	var tab = '<table class="table table-striped" id="sortableTable">';
	tab += '<thead>';
	tab += '<tr>';
	tab += '<th scope="col">Name</th>';
	tab += '<th scope="col">Address</th>';
	tab += '<th scope="col">Shared</th>';
	tab += '<th scope="col">Users</th>';
	tab += '</tr>';
	tab += '</thead>';
	tab += '</tbody>';
	
	for (var i = data.length - 1; i >= 0; i--) {
		tab += '<tr>';
		tab += '<td title="' + he.encode(data[i].getAttribute('Description')) + '" class="' + data[i].getAttribute('Status') + '" data-order="' + he.encode(data[i].getAttribute('Name')) + '" >';
		tab += '' + he.encode(data[i].getAttribute('Name')) + '' + '</td>';
		tab += '<td><a href="' + data[i].getAttribute('Address') + '" >' + data[i].getAttribute('Address') + '</a></td>';
		tab += '<td data-order="' + data[i].getAttribute('Shared') + '">' + humanFileSize(data[i].getAttribute('Shared'), true) + '</td>';
		tab += '<td>' + data[i].getAttribute('Users') + '</td>';

		tab += '</tr>';
	}

	tab += '</tbody>';
	tab += '</table>';

	document.getElementById("HublistTable").innerHTML = tab;

	$(document).ready(function() {
		$('#sortableTable').DataTable({
			"iDisplayLength": 50,
			"aLengthMenu": [[50, 100, 250, -1], [50, 100, 250, "All"]],
			"columnDefs": [
				{ "searchable": false, "targets": [2, 3] },
				{ "orderable": false, "targets": 1 },
    			{ "width": "40%", "targets": [0, 1] }
			]
		});
	} );
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
