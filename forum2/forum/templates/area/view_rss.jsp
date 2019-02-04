<%@page contentType="text/html;charset=UTF-8"%>
<%@ page import="java.util.Iterator, net.killingar.forum.internal.*, com.rsslibj.elements.Channel, webwork.util.ServletValueStack" contentType="application/rdf+xml; charset=ISO-8859-1" %><%
%><jsp:useBean class="net.killingar.forum.internal.managers.ForumManager" id="manager" scope="session" /><%

ServletValueStack vs = ServletValueStack.getStack(pageContext);

Channel channel = new Channel();
channel.setDescription("SKForum Area "+vs.findValue("area/name").toString());
channel.setLink("http://localhost/");
channel.setTitle(vs.findValue("area/name").toString());
/*channel.setImage("http://localhost/", 
				"The Channel Image", 
				"http://localhost/foo.jpg");*/

for (Iterator i = (Iterator)vs.findValue("messages"); i.hasNext(); )
{
	Message m = (Message)((ParentIDItemTreeNode)i.next()).item;

	channel.addItem("http://localhost/item"+m.getId(),
		m.getSubject(),
		m.getBody())
		.setDcContributor(manager.getUser(m.getOwnerID()).getName());
}

out.write(channel.getFeed("rdf"));

%>