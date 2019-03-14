function start_subscription_refresh() {
	setInterval(update_subscription, 2000);
}

function update_subscription() {
	var request = new XMLHttpRequest();
	request.open('GET', '/api/0/unread/', true);
	request.onload = function () {
		if (request.status === 200) {
			var response = JSON.parse(request.response);
			for (var menu_item of document.getElementsByTagName('li')) {
				var system_id = menu_item.id.split("/");
				if (system_id.length === 2) {
					var system = system_id[0];
					var id = system_id[1];
					if (response[system][id]) {
						menu_item.className = 'unread';
						// TODO: update title
					} else {
						menu_item.className = '';
					}
				}
			}
		}
	}
	request.send();
}
