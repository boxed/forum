<%@page contentType="text/html;charset=UTF-8"%>
<%@ taglib uri="wiki" prefix="wiki"  %><%@ taglib uri="sk-internal" prefix="sk" %><%@ taglib uri="webwork" prefix="ww" %>
<ww:if test="option('dynamic areas')">
	<%@ include file="dynamic-message.jsp" %>
</ww:if>
<ww:else>
	<%@ include file="message.jsp" %>
</ww:else>