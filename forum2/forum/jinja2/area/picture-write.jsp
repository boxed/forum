<%@page contentType="text/html;charset=UTF-8"%>
	<%@ include file="/htmlhead.jsp" %>
<ww:if test="replyMessageID != -1">
	<%@ include file="write.jsp" %>
</ww:if>
<ww:else>
			<title><ww:print value="area/name" /> - SKForum</title>
			<link rel="stylesheet" type="text/css" href="<ww:url value="'/forum.css'"/>"/>
		</head>
		<base target="_blank"/>
		<body onload="document.f.url.focus()">
			<center class="block">- <span class="label"><ww:print value="area/name" /></span> - <ww:if test="replyMessage"><ww:text name="'reply'"/></ww:if><ww:else><ww:text name="'speak_up'"/></ww:else> -</center>
			<sk:hr/>
			<div id="content">

			<ww:if test="hasErrorMessages">
				<ww:iterator value="errorMessages">
					<ww:print value="." /><br />
				</ww:iterator>
			</ww:if>

			<br />

			<ww:if test="warning">
				<span class="warning"><ww:print value="warning"/></span>
			</ww:if>

			<ww:if test="hasErrors">
				<ww:iterator value="errors">
					<ww:print value="." /><br />
				</ww:iterator>
			</ww:if>

			<center>
				<ww:if test="replyMessage">
					<ww:text name="'reply_to'"/>
				</ww:if>
				<ww:if test="previousMessage">
					<ww:text name="'previous_message'"/>
				</ww:if>
			</center>

			<ww:if test="replyMessage">
				<sk:hr/>
			</ww:if>

			<ww:if test="message">
				<ww:focus value="message">
					<table align="center" class="areatable">
						<ww:include value="messageView"/>
					</table>
				</ww:focus>
			</ww:if>

			<form method="post" name="f" action="<ww:print value="actionName"/>.action#firstnew" target="_self">
				<ww:if test="areaID != -1"><input type="hidden" name="areaID" value="<ww:print value="areaID"/>" /></ww:if>
				<ww:if test="messageID != -1"><input type="hidden" name="messageID" value="<ww:print value="messageID"/>" /></ww:if>
				<ww:if test="replyMessageID != -1"><input type="hidden" name="replyMessageID" value="<ww:print value="replyMessageID"/>" /></ww:if>
				<ww:if test="replyMessageTime != -1"><input type="hidden" name="replyMessageTime" value="<ww:print value="replyMessageTime"/>" /></ww:if>
				<ww:if test="time != -1"><input type="hidden" name="time" value="<ww:print value="time"/>" /></ww:if>
				<table class="widetable">
					<ww:textfield name="'url'" label="text('url')" maxlength="200" value="url" template="text-postable.jsp" />
					<ww:textfield name="'title'" label="text('title')" maxlength="200" value="title" template="text-postable.jsp" />
					<ww:textarea name="'description'" label="text('description')" rows="10" />
					<tr>
						<td></td>
						<td>
							<input id="post" type="submit" name="command" value="post" accesskey="P" class="button"/>
							<input type="submit" name="command" value="preview" class="button"/>
							<select name="postMode">
								<option label="<ww:text name="'post_mode.html'"/>" value="html"<ww:if test="postMode == 'html'"> selected="selected" </ww:if>><ww:text name="'post_mode.html'"/></option>
								<option label="<ww:text name="'post_mode.text'"/>" value="text"<ww:if test="postMode == 'text'"> selected="selected" </ww:if>><ww:text name="'post_mode.text'"/></option>
							</select>
						</td>
					</tr>
				</table>
			</form>

			<ww:if test="preview">
				<sk:hr/>
				<ww:text name="'preview'"/>:
				<ww:focus value="preview">
					<table align="center" class="areatable">
						<ww:include value="messageView"/>
					</table>
				</ww:focus>
			</ww:if>

			</div>

	<%@ include file="/htmlfoot.jsp" %>
</ww:else>
