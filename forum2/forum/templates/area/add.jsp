<%@page contentType="text/html;charset=UTF-8"%>
<%@ include file="/htmlhead.jsp" %>
    <title><ww:text name="'add_area'"/></title>
    <link rel="stylesheet" type="text/css" href="<ww:url value="'forum.css'"/>"/>
  </head>
  <body<sk:refreshcontents/>>
    <center>- <ww:text name="'add_area'"/> [<a href="<ww:url value="'faq.jsp'"><ww:param name="'topic'" value="'areas'"/></ww:url>">?</a>] -</center>
    <sk:hr />

    <form method="get">
      <ww:focus value="area">
        <input type="hidden" name="confirmed" value="true"/>
        <table class="widetable">
          <ww:textfield label="text('name')"   name="'area/name'" value="name"   />
          <tr>
            <td align="right" class="label"><ww:text name="'area_group'"/>:</td>
            <td>
              <select name="area/areaGroupID">
                <ww:iterator value="../areaGroups">
                  <ww:focus value="areaGroup">
                    <option label="<ww:print value="name"/>" value="<ww:print value="id"/>"<ww:if test="id == ../areaGroupID"> selected="selected" </ww:if>><ww:print value="indent"/><ww:print value="name"/></option>
                  </ww:focus>
                </ww:iterator>
              </select>
            </td>
          </tr>
          <tr>
            <td align="right" class="label"><ww:text name="'area_mode'"/>:</td>
            <td>
              <select name="area/mode">
                <option label="<ww:text name="'area_mode.threaded'"/>"     value="2"<ww:if test="mode == 2"> selected="selected" </ww:if>><ww:text name="'area_mode.threaded'"/></option>
                <option label="<ww:text name="'area_mode.flat'"/>"       	 value="0"<ww:if test="mode == 0"> selected="selected" </ww:if>><ww:text name="'area_mode.flat'"/></option>
                <option label="<ww:text name="'area_mode.text_archive'"/>" value="1"<ww:if test="mode == 1"> selected="selected" </ww:if>><ww:text name="'area_mode.text_archive'"/></option>
              </select>
            </td>
          </tr>
					<ww:textarea label="text('description')" name="'area/description'" value="description" rows="50" />
					<ww:textarea label="text('custom_area_data')" name="'area/custom'" value="custom" rows="50" />
          <tr><td></td><td><input type="submit" value="<ww:text name="'submit'"/>" class="button" /></td></tr>
        </table>
      </ww:focus>
    </form>

<%@ include file="/htmlfoot.jsp" %>