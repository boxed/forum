<%@page contentType="text/html;charset=UTF-8"%>
<%@ include file="/htmlhead.jsp" %><%@ page import="net.killingar.forum.internal.*" %><%
%><jsp:useBean class="net.killingar.forum.internal.managers.ForumManager" id="manager" scope="session" />
    <title><ww:print value="area/name" /></title>
    <link rel="stylesheet" type="text/css" href="<ww:url value="'/forum.css'"/>"/>
  	<base target="_blank"/>
  </head>
  <body<sk:refreshcontents/>>

		<div id="area-head-top">
			<%@ include file="area-head.jsp" %>
		</div>
		<!--
		<%
		net.killingar.forum.internal.managers.AreaManager areamgr = (net.killingar.forum.internal.managers.AreaManager)manager.getManager("net.killingar.forum.internal.managers.AreaManager");
		
		%>
		<%= AccessLevel.toString(areamgr.getUserAccess(manager.getUserID(), 3L)) %>
		<%= AccessLevel.toString(manager.getUserAccess(manager.getUserID())) %>
		-->

    <sk:hr />

		<div id="content">

		<table cellpadding="0" cellspacing="0" id="firstnewtable" align="center" class="areatable" border="0">
			<ww:iterator value="messages" status="'status'">
				<ww:if test="item">
					<ww:focus value="item">
						<!--<ww:include value="messageView"/>-->
						<ww:if test="messageView == 'default-message.jsp'">
							<%@ include file="default-message.jsp" %>
						</ww:if>
						<ww:if test="messageView == 'link-message.jsp'">
							<%@ include file="link-message.jsp" %>
						</ww:if>
						<ww:if test="messageView == 'picture-message.jsp'">
							<%@ include file="picture-message.jsp" %>
						</ww:if>
						<ww:if test="messageView == 'quote-message.jsp'">
							<%@ include file="quote-message.jsp" %>
						</ww:if>
						<ww:if test="messageView == 'tip-message.jsp'">
							<%@ include file="tip-message.jsp" %>
						</ww:if>
					</ww:focus>
				</ww:if>
			</ww:iterator>
		</table>

		</div>

    <sk:hr />

		<ww:property id="tooltipSuffix" value="'bottom'"/>
		<div id="area-head-bottom">
			<%@ include file="area-head.jsp" %>
		</div>

<%@ include file="/htmlfoot.jsp" %>