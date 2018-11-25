<%@page contentType="text/html;charset=UTF-8"%>
<ww:if test="visible == true">
	<ww:if test="../deleteAccess(.) == true">
		<sk:a value="'area.DeleteMessage.action'" cssclass="warning" target="_self" name="delete"><ww:param name="'page'" value="pageID" /><ww:param name="'messageID'" value="id" /><ww:param name="'time'" value="time"/></sk:a>
	</ww:if>
</ww:if>