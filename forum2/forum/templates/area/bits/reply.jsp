<%@page contentType="text/html;charset=UTF-8"%>
<ww:if test="area/mode == 2 && visible == true">
	<sk:areaaccess access="add message" areagroup="area/areaGroupID">
		<sk:a value="'area.WriteMessage.action'" target="_self" name="reply"><ww:param name="'replyMessageID'" value="id" /><ww:param name="'time'" value="time"/><ww:param name="'replyMessageTime'" value="lastChanged/time"/></sk:a>
	</sk:areaaccess>
</ww:if>