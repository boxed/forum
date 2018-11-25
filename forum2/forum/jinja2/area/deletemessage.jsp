<%@page contentType="text/html;charset=UTF-8"%>
<%@ include file="/htmlhead.jsp" %>
    <title><ww:text name="'confirm_message_deletion'"/></title>
    <link rel="stylesheet" type="text/css" href="<ww:url value="'forum.css'"/>"/>
  </head>
  <body>
    <center class="block">- <ww:text name="'confirm_message_deletion'"/> -</center>
    <sk:hr />

    <table align="center" class="widetable">
      <ww:focus value="message">
        <%@ include file="message.jsp" %>
      </ww:focus>
    </table>

    <sk:hr />

    <ww:text name="'really_delete_message'"/>
    [ <sk:a value="'area.DeleteMessage.action'" name="affirmative" anchor="firstnew" target="_self"><ww:param name="'page'" value="page" /><ww:param name="'delete'" value="'true'" /><ww:param name="'messageID'" value="message/id" /><ww:param name="'time'" value="time"/></sk:a> ] 
    [ <sk:a value="'area.View.action'" name="negative" anchor="firstnew" target="_self"><ww:param name="'page'" value="page" /><ww:param name="'areaID'" value="message/areaID" /><ww:param name="'time'" value="time"/></sk:a> ]
      
<%@ include file="/htmlfoot.jsp" %>