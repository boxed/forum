<%@page contentType="text/html;charset=UTF-8"%>
<ww:if test="editable(id) == true">
	<sk:a value="'area.EditMessage.action'" target="_self" name="edit"><ww:param name="'messageID'" value="id" /><ww:param name="'time'" value="time"/></sk:a>
</ww:if>