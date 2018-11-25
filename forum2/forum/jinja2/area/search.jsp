<%@page contentType="text/html;charset=UTF-8"%>
<%@ include file="/htmlhead.jsp" %>
    <title>search <ww:print value="area/name" /></title>
    <link rel="stylesheet" type="text/css" href="<ww:url value="'forum.css'"/>"/>
  </head>
  <body>
    <center><b>search <ww:print value="area/name" /></b> - [<a href="<ww:url value="'faq.jsp'"><ww:param name="'topic'" value="'areas'"/></ww:url>" target="_self">?</a>]</center>
    <sk:hr />
    <form method="post" target="_self">
      <input type="hidden" name="areaID" value="<ww:print value="area/id" />" />
      <table class="widetable">
        <ww:textfield name="'search'" label="text('search_for')" value="search" />
				<ww:textfield name="'username'" label="text('search_by_user')" value="username" />
				<tr><td></td><td><input class="optionbox" type="radio" name="searchType" id="searchType1" value="1"<ww:if test="searchType == 1"> checked="checked"</ww:if>/><label style="display: inline;" for="searchType1"><ww:print value="text('search_this_area')"/></label></td></tr>
				<tr><td></td><td><input class="optionbox" type="radio" name="searchType" id="searchType3" value="3"<ww:if test="searchType == 3"> checked="checked"</ww:if>/><label style="display: inline;" for="searchType3"><ww:print value="text('search_areagroup')"/></label></td></tr>
				<tr><td></td><td><input class="optionbox" type="radio" name="searchType" id="searchType2" value="2"<ww:if test="searchType == 2"> checked="checked"</ww:if>/><label style="display: inline;" for="searchType2"><ww:print value="text('search_all_areas')"/></label></td></tr>
				
        <tr><td></td><td><input type="submit" value="<ww:print value="text('search')"/>" class="button" /></td></tr>
      </table>
    </form>

		<ww:print value="text('search_number_of_hits')"/> <ww:print value="numberOfHits" />

    <center><b><ww:print value="area/name" /></b> - <ww:text name="'search_result'"/></center>
    <sk:hr />
    <table align="center" class="widetable">
      <ww:iterator value="messages">
				<tr><td>&nbsp;</td></tr>
				<tr>
					<td>
						<ww:if test="searchType != 1">
							<ww:text name="'area'"/>: <a href="<ww:url value="'area.View.action'"><ww:param name="'areaID'" value="areaID" /></ww:url><sk:scroll />"><ww:print value="area(areaID)/name"/></a>
						</ww:if>
						[ <a href="<ww:url value="'area.View.action'"><ww:param name="'areaID'" value="areaID" /><ww:param name="'gotoMessageID'" value="id" /></ww:url>#<ww:print value="id"/>"><ww:text name="'go_to_message'"/></a> ]
					</td>
				</tr>
        <%@ include file="message.jsp" %>
      </ww:iterator>
    </table>

<%@ include file="/htmlfoot.jsp" %>