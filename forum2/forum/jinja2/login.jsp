<%@page contentType="text/html;charset=UTF-8"%>
<%@ include file="/htmlhead.jsp" %>
    <title> - SKForum - </title>
    <link rel="stylesheet" type="text/css" href="<ww:url value="'sk.css'"/>"/>
  </head>
  <body onload="document.f.username.focus()">
    <center>login to the <a href="<ww:url value="'http://satans.killingar.net'"/>">SK</a> forum</center>
    <sk:hr />

    <form method="post" action="<ww:url value="'Login.action'"/>" name="f">
      <input type="hidden" name="url" value="<ww:print value="url"/>" />
      <table align="center" style="width: 300px;">
				<tr><td colspan="2" align="center"><span class="label">warning:</span> password is sent in plain text</td></tr>
				<tr><td colspan="2">&nbsp;</td></tr>
        <ww:if test="hasErrorMessages">
          <ww:iterator value="errorMessages">
            <tr><td colspan="2" align="center"><ww:print value="." /></td></tr>
          </ww:iterator>
        </ww:if>
        <ww:textfield name="'username'" label="'username'" maxlength="32"/>
        <ww:password name="'password'" label="'password'" maxlength="32"/>
        <tr><td colspan="2" align="right"><input type="submit" value="login" class="button" /></td></tr>
        <tr><td colspan="2">&nbsp;</td></tr>
				<tr><td colspan="2" align="right">
					this page uses a session cookie <br />
					<a href="cookies.jsp">read more</a>
				</td></tr>
				<tr><td colspan="2">&nbsp;</td></tr>
				<tr><td colspan="2" align="right"><a href="ForgotPassword.action">forgot your password?</a></td></tr>
				<tr><td colspan="2" align="right"><a href="CreateAccount.action">create account</a></td></tr>
      </table>
    </form>
		
		<div align="right">powered by <a href="http://soft.killingar.net?wiki=skforum">SKForum</a></div>
		
<%@ include file="/htmlfoot.jsp" %>