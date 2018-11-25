<%@page contentType="text/html;charset=UTF-8"%>
<ww:if test="currentUser/id == ownerID">
	<ww:property id="currentUserCSS" value="'currentuser'"/>
</ww:if>
<ww:else>
	<ww:property id="currentUserCSS" value="'otheruser'"/>
</ww:else>

<tr id="subject_tr<ww:print value="id"/>" class="message <ww:print value="@currentUserCSS"/> level<ww:print value="indent"/>">
	<%-- message subject line --%>
  <td style="padding-left: <sk:indent/>px;" onClick="javascript:collapseExpand('<ww:print value="id"/>')">

		<div class="subject<ww:print value="cssClass(.)"/>">

			<span id="expandIcon<ww:print value="id"/>">
				-
			</span>
			<span id="collapseIcon<ww:print value="id"/>" style="display:none;">
				+
			</span>

				

			<ww:if test="area/mode == 1">
			    <%-- if text archive --%>
				<span class="label"><ww:print value="subject" /></span><br />
				<ww:text name="text('no_words')" value0="noWords" />
			</ww:if>


			<ww:else>
			    <%-- if normal flat or threaded area --%>
				<span class="label"><ww:print value="subject" /></span>
			</ww:else>

			<%-- written by --%>
			- <sk:user value="ownerID" />

			<%-- deleted --%>
			<ww:if test="visible == false">
				<td class="right-margin">
					<%@ include file="bits/deleted.jsp" %>
				</td>
			</ww:if>

			<%-- first new anchor --%>
			<ww:if test="areaInfo/firstnewID == id">
				<a name="firstnew" id="firstnew" />
			</ww:if>

			<a name="<ww:print value="id" />" />
		</div>
  </td>
  <td width="60" valign="top" class="right-margin-top <ww:print value="@currentUserCSS"/><ww:print value="cssClass(.)"/>">

    <%-- time --%>
    <span class="time"><ww:date value="timecreated"/></span>

	</td>
	<ww:if test="area/mode == 2">
		<td style="width: 40px;" valign="top" class="right-margin-top <ww:print value="@currentUserCSS"/> <ww:print value="cssClass(.)"/>"><%@ include file="bits/reply.jsp" %></td>
  </ww:if>

  <td style="width: 50px;"  valign="top" class="right-margin-top <ww:print value="@currentUserCSS"/> <ww:print value="cssClass(.)"/>"><%@ include file="bits/unread_from_here.jsp" %></td>
  <td style="width: 40px;"  valign="top" class="right-margin-top <ww:print value="@currentUserCSS"/> <ww:print value="cssClass(.)"/>"><%@ include file="bits/edit.jsp" %>&nbsp;</td>
  <td style="width: 30px;"  valign="top" class="right-margin-top right-margin-top-left <ww:print value="@currentUserCSS"/> <ww:print value="cssClass(.)"/>"><%@ include file="bits/del.jsp" %>&nbsp;</td>
</tr>
<tr id="body_tr<ww:print value="id"/>" class="message level<ww:print value="indent"/>">
	<ww:if test="bodyEmpty(.) == false">
		<%-- message body --%>
		<td style="padding-left: <sk:indent/>px;"  class="body <ww:print value="@currentUserCSS"/>" colspan="<ww:if test="visible == false">5</ww:if><ww:else>6</ww:else>">
			<div class="innerbody<ww:print value="cssClass(.)"/>"><sk:pre><ww:print value="body" /></sk:pre>&nbsp;</div><br />
		</td>
	</ww:if>
	<ww:else>
		<td style="padding-left: <sk:indent/>px;"   class="<ww:print value="@currentUserCSS"/>" colspan="<ww:if test="visible == false">5</ww:if><ww:else>6</ww:else>">
			<div class="nobody">&nbsp;</div>
		</td>
	</ww:else>
</tr>
