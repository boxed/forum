<%@page contentType="text/html;charset=UTF-8"%>
<center id="area-head" class="block">
	<div id="area-head-block1">
		<span class="label <ww:if test="unread == true">unread</ww:if><ww:else>odd</ww:else><ww:if test="area/description"> moreinfo</ww:if>"
			<ww:if test="area/description">OnMouseOver="javascript:show('tooltipArea<ww:print value="area/id"/><ww:print value="@tooltipSuffix"/>', 'inline');" OnMouseOut="javascript:hide('tooltipArea<ww:print value="area/id"/>');"</ww:if>>
			<div id="tooltipArea<ww:print value="area/id"/><ww:print value="@tooltipSuffix"/>" class="tooltip" OnMouseOut="javascript:hide('tooltipArea<ww:print value="area/id"/>');"><span class="label"><ww:print value="area/name" /></span><p /><sk:pre><ww:print value="area/description"/></sk:pre></div>
			<ww:print value="area/name" />
		</span>

		<%-- subscription status --%>
		<ww:if test="manager/areaHotlistManager/hasArea(area/id) == true">
			<a href="<ww:url value="'hotlist.Remove.action'"><ww:param name="'areaID'" value="area/id"/></ww:url>">-</a>
		</ww:if>
		<ww:else>
			<a href="<ww:url value="'hotlist.Add.action'"><ww:param name="'areaID'" value="area/id"/></ww:url>">+</a>
		</ww:else>

		<%-- faq --%>
		[<a href="<ww:url value="'faq.jsp'"><ww:param name="'topic'" value="'areas'" /></ww:url>" target="_self">?</a>] 

		<%-- show hidden --%>
		<ww:if test="showHidden == false">
			[ <sk:a value="'area.View.action'" name="show_deleted" target="_self" anchor="firstnew"><ww:param name="'areaID'" value="area/id"/><ww:param name="'time'" value="time"/><ww:param name="'page'" value="pageID"/><ww:param name="'showHidden'" value="true"/></sk:a> ] 
		</ww:if>
		<ww:else>
			[ <sk:a value="'area.View.action'" name="hide_deleted" target="_self" anchor="firstnew"><ww:param name="'areaID'" value="area/id"/><ww:param name="'time'" value="time"/><ww:param name="'page'" value="pageID"/><ww:param name="'showHidden'" value="false"/></sk:a> ]
		</ww:else>

		<%-- keep unread --%>
		<ww:if test="showingUnread == true">
			[ <sk:a value="'area.View.action'" name="keep_unread" target="_self" anchor="firstnew"><ww:param name="'areaID'" value="area/id"/><ww:param name="'setTime'" value="time"/><ww:param name="'page'" value="pageID"/></sk:a> ]
		</ww:if>

		<%-- search --%>
		[ <sk:a value="'area.Search.action'" name="search" target="_self"><ww:param name="'areaID'" value="area/id"/></sk:a> ]

		<ww:text name="'page'"/> <ww:if test="startPage != endPage"><ww:print value="startPage"/>-</ww:if><ww:print value="endPage"/>/<ww:print value="numberOfPages" /> 

		<%-- write --%>
		<sk:areaaccess access="add message" areagroup="area/areaGroupID">
			- <sk:a value="'area.WriteMessage.action'" name="speak_up" target="_self"><ww:param name="'areaID'" value="area/id"/><ww:param name="'time'" value="time"/></sk:a>
		</sk:areaaccess>

		<ww:if test="startPage != 1 || endPage != lastPage">
			<sk:hr />
		</ww:if>
	</div>

	<div id="area-head-block2">
		<%-- first & prev --%>
		<ww:if test="startPageID != 0">
			[ <sk:a value="'area.View.action'" name="first" target="_self" anchor="firstnew"><ww:param name="'showHidden'" value="showHidden"/><ww:param name="'areaID'" value="area/id"/><ww:param name="'page'" value="0"/><ww:param name="'time'" value="time"/></sk:a> ]

			[ <sk:a value="'area.View.action'" name="prev" target="_self" anchor="firstnew"><ww:param name="'showHidden'" value="showHidden"/><ww:param name="'areaID'" value="area/id"/><ww:param name="'page'" value="prevPage"/><ww:param name="'time'" value="time"/></sk:a> ]
		</ww:if>

		<%-- next & latest --%>
		<ww:if test="pageID != lastPage">
			[ <sk:a value="'area.View.action'" name="next" target="_self" anchor="firstnew"><ww:param name="'showHidden'" value="showHidden"/><ww:param name="'areaID'" value="area/id"/><ww:param name="'page'" value="nextPage"/><ww:param name="'time'" value="time"/></sk:a> ]

			[ <sk:a value="'area.View.action'" name="latest" target="_self" anchor="firstnew"><ww:param name="'showHidden'" value="showHidden"/><ww:param name="'areaID'" value="area/id"/><ww:param name="'page'" value="lastPage"/><ww:param name="'time'" value="time"/></sk:a> ]
		</ww:if>
	</div>

</center>