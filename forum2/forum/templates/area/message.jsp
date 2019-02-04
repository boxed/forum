<%@page contentType="text/html;charset=UTF-8"%>
<ww:if test="currentUser/id == ownerID">
	<ww:property id="currentUserCSS" value="'currentuser'"/>
</ww:if>
<ww:else>
	<ww:property id="currentUserCSS" value="'otheruser'"/>
</ww:else>

<tr id="subject_tr<ww:print value="id"/>" class="message <ww:print value="@currentUserCSS"/> level<ww:print value="indent"/>">
	<%-- message subject line --%>
  <td colspan="5" style="padding-left: <sk:indent/>px;" class="<ww:print value="@currentUserCSS"/>">

		<div class="subject<ww:print value="cssClass(.)"/>">
	
			<%-- if text archive --%>
			<ww:if test="area/mode == 1">
				<span class="label"><ww:print value="subject" /><br />
				<ww:print value="noWords" /></span> words
			</ww:if>

			<%-- if normal flat or threaded area --%>
			<ww:else>
				<span class="label"><ww:print value="subject" /></span>
			</ww:else>

			<%-- written by --%>
			- <sk:user value="ownerID" /> 

			<%-- first new anchor --%>
			<ww:if test="areaInfo/firstnewID == id">
				<a name="firstnew" id="firstnew" />
			</ww:if>

			<a name="<ww:print value="id" />" />
		</div>
  </td>
  <td valign="top" class="right-margin-top <ww:print value="@currentUserCSS"/><ww:print value="cssClass(.)"/>">

    <%-- time --%>
		<div>
    	<span class="time"><ww:date value="timecreated"/></span>&nbsp;
		</div>

  </td>
</tr>
<tr id="body_tr<ww:print value="id"/>" class="message level<ww:print value="indent"/>">
	<%-- message body --%>
  <td colspan="5" style="padding-left: <sk:indent/>px;" class="body <ww:print value="@currentUserCSS"/>">
    <div class="innerbody<ww:print value="cssClass(.)"/>"><sk:pre><ww:print value="body" /></sk:pre>&nbsp;</div>
		<br />
		<ww:if test="../bodyEmpty(.) == false"><br /></ww:if>
  </td>
  <td valign="top" class="right-margin <ww:print value="@currentUserCSS"/><ww:print value="cssClass(.)"/>">
		<div>
			<%@ include file="bits/reply.jsp" %>
			<%@ include file="bits/edit.jsp" %>
			<%@ include file="bits/unread_from_here.jsp" %>
			<%@ include file="bits/del.jsp" %>
			<%@ include file="bits/deleted.jsp" %>
		</div>
  </td>
</tr>