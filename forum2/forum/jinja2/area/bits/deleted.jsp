<%@page contentType="text/html;charset=UTF-8"%>
<ww:if test="visible == false">
	<ww:text name="'deleted_by'"/>: <br /> <sk:user value="lastChangedUserID"/>
</ww:if>