<%@page contentType="text/html;charset=UTF-8"%>
<%@ taglib uri="wiki" prefix="wiki"  %><%@ taglib uri="sk-internal" prefix="sk" %><%@ taglib uri="webwork" prefix="ww" %>
<ww:if test="indent == 0 && splitBody/param('description')">
	<ww:if test="currentUser/id == ownerID">
		<ww:property id="currentUserCSS" value="'currentuser'"/>
	</ww:if>
	<ww:else>
		<ww:property id="currentUserCSS" value="'otheruser'"/>
	</ww:else>
	
	<tr id="subject_tr<ww:print value="id"/>" class="message <ww:print value="@currentUserCSS"/> level<ww:print value="indent"/>">
		<%-- message subject line --%>
		<td colspan="5" class="<ww:print value="@currentUserCSS"/>">
	
			<div class="subject<ww:print value="cssClass(.)"/>">
				<ww:if test="splitBody/param('filename')">
					<ww:print value="splitBody/param('title')"/>
				</ww:if>
				<ww:else>
					<ww:print value="subject"/></a>
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
			<div class="<ww:print value="cssClass(.)"/>">
				<span class="time"><ww:date value="timecreated"/></span>&nbsp;
			</div>
	
		</td>
	</tr>
	<tr id="body_tr<ww:print value="id"/>" class="message level<ww:print value="indent"/>">
		<%-- message body --%>
		<td colspan="5" style="" class="body <ww:print value="@currentUserCSS"/> <ww:print value="cssClass(.)"/>">
			<ww:if test="splitBody/param('filename')">
				<table class="widetable">
					<tr>
						<td style="width: 100px; height: 100px;">
							<a href="<ww:print value="splitBody/param('url')"/>">
								<img src="<ww:print value="areaCustomizer/thumbnail(splitBody/param('filename'))"/>" />
							</a>
						</td>
						<td>
							<ww:print value="splitBody/param('description')"/>
						</td>
					</tr>
        </table>
			</ww:if>
			<ww:else>
				<ww:print value="body"/>
			</ww:else>
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
</ww:if>
<ww:else>
	<%@ include file="default-message.jsp" %>
</ww:else>