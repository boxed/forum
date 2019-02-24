function formKeyboardHandler(f, event)
{ 
	if (event.ctrlKey && 13 === event.keyCode)
	{ 
		if (f.post)
			f.post.click();
		else
			f.submit(); 
		return false; 
	} 
	return true; 
} 

function addClassToID(id, cl)
{
	document.getElementById(id).className += " "+cl;
}

function addClassToObject(o, cl)
{
	o.className += " "+cl;
}

function removeClass(cl, classNames)
{
	var s = classNames.split(" ");
	var r = "";
	for (var i = 0; i != s.length; i++)
	{
		if (s[i] != cl)
			r += s[i]+" ";
	}

	return r;
}

function removeClassFromID(id, cl)
{
	removeClassFromObject(document.getElementById(id));
}

function removeClassFromObject(o, cl)
{
	o.className = removeClass(cl, o.className);
}

function getIndentFromElement(e)
{
	return e.getElementsByTagName('td')[0].style.paddingLeft;
}

function collapseExpand(item)
{
	var element = document.getElementById("body_tr"+item);
	var startIndent = getIndentFromElement(element);

	if (element.style.display === "none") // show
	{
		var disp = document.getElementById("subject_tr"+item).style.display;
		element.style.display = document.getElementById("subject_tr"+item).style.display;
		for (var e = element.nextSibling; e != null; e = e.nextSibling)
		{
			if (e.getAttribute && getIndentFromElement(e) <= startIndent)
				break;

			if (e.style)
				e.style.display = disp;
		}
		document.getElementById("collapseIcon"+item).style.display = "none";
		document.getElementById("expandIcon"+item).style.display = "inline";
	}
	else // hide
	{
		for (var e = element.nextSibling; e != null; e = e.nextSibling)
		{
			if (e.getAttribute && getIndentFromElement(e) <= startIndent)
				break;

			if (e.style)
				e.style.display = "none";
		}
		element.style.display = "none"
		document.getElementById("collapseIcon"+item).style.display = "inline";
		document.getElementById("expandIcon"+item).style.display = "none";
	}	
}

function show(item)
{
	document.getElementById(item).style.display = "";
}

function show(item, type)
{
	if (!document.getElementById(item))
		alert("error 1 "+item);
	if (!document.getElementById(item).style)
		alert("error 2 "+item);
	document.getElementById(item).style.display = type;
}

function hide(item)
{
	document.getElementById(item).style.display = "none";
}

function reload(iFrame)
{
	var foo = document.getElementById(iFrame).src;
	document.getElementById(iFrame).src = "about:blank";
	document.getElementById(iFrame).src = foo;
}

function dynamicLoad(iFrame)
{
	var frm = document.getElementById(iFrame);
	var data;
	if (frm.contentDocument)
		data = frm.contentDocument.body.innerHTML;
	else if (frm.contentWindow)
		data = frm.contentWindow.document.body.innerHTML;
	else if (frm.document)
		data = frm.document.body.innerHTML;
  var commands = data.split(";");
  for (var i = 0; i != commands.length; i++)
  {
    eval(commands[i]);
  }

  //self.setTimeout("reload(""+iFrame+"")", 10000); // reload dynamic data every 10 secs
}

function makeUnread(item)
{
	document.getElementById(item).className = "unread";
	// add unread class, but keep the old classes
	show(item);
}

/*function makeRead(item)
{
  // FIXME this won"t work unless we remove unread class, but keep the other classes
  // hidden if this is a passive entry
}*/

function loadXMLDoc(url, eventHandler)
{
	var req;
	
	// branch for native XMLHttpRequest object
	if (window.XMLHttpRequest)
	{
		req = new XMLHttpRequest();
		if (eventHandler)
			req.onreadystatechange = function() { if (req.readyState === 4) eventHandler(req); };
		req.open("GET", url, true);
		req.send(null);
	}
	// branch for IE/Windows ActiveX version
	else if (window.ActiveXObject)
	{
		req = new ActiveXObject("Microsoft.XMLHTTP");
		if (req)
		{
			req.onreadystatechange = function() { if (req.readyState === 4) eventHandler(req); };
			req.open("GET", url, true);
			req.send();
		}
	}
}
