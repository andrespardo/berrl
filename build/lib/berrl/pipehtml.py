import os
import json
import itertools

# makes start block from template using 
def make_startingblock(apikey,sidebar,file_dictionary):
	sidebarstring1 = '''
<div id="sidebar">
    <h1>leaflet-sidebar</h1>
</div>
'''
	sidebarstring2 = '''
var sidebar = L.control.sidebar('sidebar', {
    position: 'left'
});

map.addControl(sidebar);
setTimeout(function () {
    sidebar.show();
}, 500);
'''

	if not sidebar == True:
		sidebarstring1,sidebarstring2 = '',''
	# logic for if legend is empty string variable
	
	startingblock = """
<html>
<head>
<meta charset=utf-8 />
<title>PipeGeoJSON Demo</title>
<meta name='viewport' content='initial-scale=1,maximum-scale=1,user-scalable=no' />
<script src='https://api.tiles.mapbox.com/mapbox.js/v2.2.4/mapbox.js'></script>
<link href='https://api.tiles.mapbox.com/mapbox.js/v2.2.4/mapbox.css' rel='stylesheet' />
<script src="https://api.mapbox.com/mapbox.js/v2.2.4/mapbox.js"></script>
<script src="http://code.jquery.com/jquery-1.11.3.min.js"></script>
<link href='https://api.mapbox.com/mapbox.js/v2.2.4/mapbox.css' rel='stylesheet' />
<link href='https://api.tiles.mapbox.com/mapbox.js/v2.2.4/mapbox.css' rel='stylesheet' />
<script src='https://api.mapbox.com/mapbox.js/plugins/leaflet-omnivore/v0.2.0/leaflet-omnivore.min.js'></script>
<script src="https://d3js.org/d3.v3.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery-nstslider/1.0.13/jquery.nstSlider.js"></script>
<link href='https://cdnjs.cloudflare.com/ajax/libs/jquery-nstslider/1.0.13/jquery.nstSlider.min.css' rel='stylesheet' />
<script src="https://cdn.rawgit.com/Turbo87/leaflet-sidebar/master/src/L.Control.Sidebar.js"></script>
<link href='https://cdn.rawgit.com/Turbo87/leaflet-sidebar/master/src/L.Control.Sidebar.css' rel='stylesheet' />
<script src="https://d3js.org/d3.v3.min.js"></script>

<style>
  body { margin:0; padding:0; }
  #map { position:absolute; top:0; bottom:0; width:100%; }
</style>
</head>
<body>
<style>
table, th, td {
    border: 1px solid black;
}
</style>




"""	
	startingblock2 = """""
<div id='map'></div>

%s

<script>
L.mapbox.accessToken = 'xxxxx';""""" % (sidebarstring1)
	startingblock2 = startingblock2.replace('xxxxx',apikey)



	startingblock3 = """
\nvar map = L.mapbox.map('map', 'mapbox.streets',{
    zoom: 5
    });

%s

// omnivore will AJAX-request this file behind the scenes and parse it: 

// note that there are considerations:
// - The file must either be on the same domain as the page that requests it,
//   or both the server it is requested from and the user's browser must
//   support CORS.

// Internally this uses the toGeoJSON library to decode the KML file
// into GeoJSON




\n""" % sidebarstring2
	
	block = startingblock + startingblock2 + startingblock3

	
	# sending arguemnts to make startingblock3 block
	if file_dictionary == False:
		return block
	else:
		block = block + make_startingblock3_filter(file_dictionary)
	

	
	return block

# makes the inner html that will be appended to colorkey ul
def make_drop_down_html2(filter_file_dictionary):
	combinedtotal = []
	sliders = []
	uniques = []
	for row in filter_file_dictionary.keys():
		if 'slider_' in str(row):
			sliders.append(row)
	
	for row in filter_file_dictionary.keys():
		if not 'slider_' in str(row) and not 'zooms' == row and not 'colorkeyfields' == row and not str(row) == 'chart_dictionary': 
			# getting the drop down fields for each key value in dict
			fields = filter_file_dictionary[str(row)]

			# setting column equal to the key value or a column in a df
			column = str(row)

			# making starting html block
			start = '''"<br><b>%s</b><select id='%s' name='mapStyle' value='dark' style='font-size: 20px;'>''' % (column,column)
			allfield = """\t<option value='dark-nolabel'>ALL</option>"""
			total = start + allfield
			for row in fields:
				newrow = """\t<option value='dark-nolabel'>%s</option>""" % row
				total += newrow
			total = total + '</select><br><br>'
			total = total + '"'
			combinedtotal.append(total)
			uniques.append(row)

	for row in sliders:
		column = str.split(row,'_')[-1]
		min,max = filter_file_dictionary[str(row)]
		if not row == sliders[-1]:
			total = '''"<b>%s</b><div class='nstSlider' div id = '%s' data-range_min='%s' data-range_max='%s' data-cur_min='%s'    data-cur_max='%s'><div class='bar'></div><div class='leftGrip'></div><div class='rightGrip'></div></div><div class='leftLabel%s' /><div class='rightLabel%s' />"''' % (column,column,min,max,min,max,column,column)
		else:
			total = '''"<b>%s</b><div class='nstSlider' div id = '%s' data-range_min='%s' data-range_max='%s' data-cur_min='%s'    data-cur_max='%s'><div class='bar'></div><div class='leftGrip'></div><div class='rightGrip'></div></div><div class='leftLabel' /><div class='rightLabel' />"''' % (column,column,min,max,min,max)
		combinedtotal.append(total)
		uniques.append(row)
	return combinedtotal,uniques


# makes the raw line that be added in the js to instantiate dropdown menu
def make_startingblock3_filter(filter_dictionary):
	total = []
	totaluniques = []
	for row in filter_dictionary.keys():
		filter_file_dictionary = filter_dictionary[str(row)]
		total_temp,uniques = make_drop_down_html2(filter_file_dictionary)
		for a,unique in itertools.izip(total_temp,uniques):
			ind = 0
			for row in totaluniques:
				if row == unique:
					ind = 1
			if not ind == 1:
				total.append(a)
				totaluniques.append(unique)
	combinedtotal = ''
	for row in total:
		total = "$('#sidebar').append(%s)\n" % row
		combinedtotal += total
	return combinedtotal

# makes the string to retrieve the drop down menus for the appropriate geojson file
def make_filter_varstring(filter_file_dictionary):
	total = ''
	count = 0
	for row in filter_file_dictionary.keys():
		count +=1
		if not 'slider_' in str(row) and not str(row) == 'zooms' and not str(row) == 'colorkeyfields' and not str(row) == 'chart_dictionary':
			temp = '''\t\tvar skillsSelect = document.getElementById("%s");\n\t\t\tvar selectedText%s = skillsSelect.options[skillsSelect.selectedIndex].text;\n''' % (str(row),count)
			total += temp
	return total[2:]

def get_slider_bool(filter_file_dictionary):
	sliderbool = False
	for row in filter_file_dictionary.keys():
		if 'slider_' in str(row):
			sliderbool = str.split(row,'_')[-1]
	return sliderbool

# makes the logic string for zoom block pertaining to drop down menus and sliders (later)
def make_logicstring(filter_file_dictionary):
	count = 0 
	total = ''
	sliders = []
	for row in filter_file_dictionary.keys():
		if 'slider_' in str(row):
			sliders.append(row)
	
	for row in filter_file_dictionary.keys():
		count += 1
		if not 'slider_' in str(row) and not str(row) == 'zooms' and not str(row) == 'colorkeyfields' and not str(row) == 'chart_dictionary':
			temp = '''&&((layer.feature.properties['%s'].toString()==selectedText%s)||(selectedText%s=='ALL'))''' % (str(row),count,count)
			total += temp
	count = 0
	for row in sliders:
		count += 1
		field = str.split(row,'_')[-1]
		min,max = filter_file_dictionary[str(row)]
		if not row == sliders[-1]:
			temp = '''&&((layer.feature.properties['%s'] >= parseInt(leftValue%s))&&(layer.feature.properties['%s'] <= parseInt(rightValue%s)))''' % (field,field,field,field)
		else:
			temp = '''&&((layer.feature.properties['%s'] >= parseInt(leftValue))&&(layer.feature.properties['%s'] <= parseInt(rightValue)))''' % (field,field)

		total += temp
	total = total[2:]

	total = '(' + total + ')'
	return total


def skew_tempblock(tempblock,count):
	tempblock = str.split(tempblock,'\n')
	newtempblock = ''
	for row in tempblock:
		row = '\t'*(count - 1)*2 + row + '\n'
		newtempblock += row
	return newtempblock

# if zoom block string is needed with a file filter kwarg input this parses the changed lines and 
# implements them into existing zoom block code
def make_zoom_block_filter(min,max,filter_file_dictionary):
	varstring = make_filter_varstring(filter_file_dictionary)
	logicstring = make_logicstring(filter_file_dictionary)
	sliderbool = get_slider_bool(filter_file_dictionary)
	if sliderbool == False:
		block = '''
	map.on('dragend',function(e) {
		%s
		var outerbounds = [[map.getBounds()._southWest.lng,map.getBounds()._northEast.lat],[map.getBounds()._northEast.lng,map.getBounds()._southWest.lat]]
		var outerbounds = L.bounds(outerbounds[0],outerbounds[1]);
		dataLayer.eachLayer(function(layer) {
			if (((outerbounds.contains(layer.feature.properties['bounds']) == true)||(outerbounds.intersects(layer.feature.properties['bounds']) == true))&&((map.getZoom() >= %s)&&(map.getZoom() <= %s))&&%s) { 
				layer.addTo(map) 
				console.log('added')
			}
			else {
				if ( dataLayer.hasLayer(layer) == true ) {
					map.removeLayer(layer)
				}
			}
		})
	});''' % (varstring,str(min),str(max),logicstring)
	else:
		# making a list for seperate sliders to parse into one block string
		sliders = []
		for row in filter_file_dictionary.keys():
			if 'slider_' in str(row) and not 'chart_dictionary'==row:
				sliders.append(row)

		if not len(sliders) == 1:
			block1 = '''
		map.on('dragend',function(e) {
			%s
			var outerbounds = [[map.getBounds()._southWest.lng,map.getBounds()._northEast.lat],[map.getBounds()._northEast.lng,map.getBounds()._southWest.lat]]
			var outerbounds = L.bounds(outerbounds[0],outerbounds[1]);
			''' % varstring
			

			count = 0
			total = ''
			for row in sliders:
				field = str.split(row,'_')[-1]
				count += 1
				# logic for if the slider argument field isnt the last in the dictionary
				if not sliders[-1] == row:
					tempblock ='''
			$('#%s').nstSlider({
				"crossable_handles": false,
				"left_grip_selector": ".leftGrip",
				"right_grip_selector": ".rightGrip",
				"value_bar_selector": ".bar",
				"value_changed_callback": function(cause, leftValue, rightValue) {
					$(this).parent().find('.leftLabel%s').text(leftValue)
					$(this).parent().find('.rightLabel%s').text(rightValue)
					var leftValue%s = leftValue;
					var rightValue%s = rightValue;
			'''	% (field,field,field,field,field)
					# logic for if the splider block count is above 1 and 
					# needs to be skewed a tab over (not necessarily necessary but cleaner)
					if not count == 1:
						tempblock = skew_tempblock(tempblock,count)
				else:
					tempblock ='''
			$('#%s').nstSlider({
				"crossable_handles": false,
				"left_grip_selector": ".leftGrip",
				"right_grip_selector": ".rightGrip",
				"value_bar_selector": ".bar",
				"value_changed_callback": function(cause, leftValue, rightValue) {
					$(this).parent().find('.leftLabel').text(leftValue)
					$(this).parent().find('.rightLabel').text(rightValue)
			'''	% (field)
					tempblock = skew_tempblock(tempblock,count)
				total += tempblock
					
			finalblock = '''		
					dataLayer.eachLayer(function(layer) {
						if (((outerbounds.contains(layer.feature.properties['bounds']) == true)||(outerbounds.intersects(layer.feature.properties['bounds']) == true))&&((map.getZoom() >= %s)&&(map.getZoom() <= %s))&&%s) { 
							layer.addTo(map) 
							console.log('added')
						}
						else {
							if ( dataLayer.hasLayer(layer) == true ) {
								map.removeLayer(layer)
							}
						}
					})
					}
		})''' % (str(min),str(max),logicstring)	
			finalblock = skew_tempblock(finalblock,count)

			ending = '\t\t}\n\t\t})\n' * (count - 1) + '\t});'

			block = block1 + '\n' + total  + finalblock + ending
		else:
			block = '''
	map.on('dragend',function(e) {
		%s
		var outerbounds = [[map.getBounds()._southWest.lng,map.getBounds()._northEast.lat],[map.getBounds()._northEast.lng,map.getBounds()._southWest.lat]]
		var outerbounds = L.bounds(outerbounds[0],outerbounds[1]);
		$('#%s').nstSlider({
			"crossable_handles": false,
			"left_grip_selector": ".leftGrip",
			"right_grip_selector": ".rightGrip",
			"value_bar_selector": ".bar",
			"value_changed_callback": function(cause, leftValue, rightValue) {
				$(this).parent().find('.leftLabel').text(leftValue)
				$(this).parent().find('.rightLabel').text(rightValue)
				dataLayer.eachLayer(function(layer) {
					if (((outerbounds.contains(layer.feature.properties['bounds']) == true)||(outerbounds.intersects(layer.feature.properties['bounds']) == true))&&((map.getZoom() >= %s)&&(map.getZoom() <= %s))&&%s) { 
						layer.addTo(map) 
						console.log('added')
					}
					else {
						if ( dataLayer.hasLayer(layer) == true ) {
							map.removeLayer(layer)
						}
					}
				})
				}
	})
	});''' % (varstring,sliderbool,str(min),str(max),logicstring)
	return block



# given a minimum and maximum zoom range
# returns block of js that corresponds to zoom dependent control
def make_zoom_block(min,max,count,colorkeyfields,bounds,filter_file_dictionary):

	if min == '' and max == '' and not bounds == True:
		return ''


	if colorkeyfields == False and bounds == False:
		block = '''
		map.on('zoomend', function(e) {
			if ( (map.getZoom() >= %s)&&(map.getZoom() <= %s) ){ 
				if (map.hasLayer(dataLayer) != true) {
					add%s()		
				}
			}
			else { map.removeLayer( dataLayer ) }
		})''' % (str(min),str(max),str(count))
	elif bounds == True:
		if min == '' and max == '':
			min,max = [0,20]
		if filter_file_dictionary == False:
			block = '''
	map.on('dragend',function(e) {
		var outerbounds = [[map.getBounds()._southWest.lng,map.getBounds()._northEast.lat],[map.getBounds()._northEast.lng,map.getBounds()._southWest.lat]]
		var outerbounds = L.bounds(outerbounds[0],outerbounds[1]);
		dataLayer.eachLayer(function(layer) {
			if (((outerbounds.contains(layer.feature.properties['bounds']) == true)||(outerbounds.intersects(layer.feature.properties['bounds']) == true))&&((map.getZoom() >= %s)&&(map.getZoom() <= %s))) { 
				layer.addTo(map) 
				console.log('added')
			}
			else {
				if ( dataLayer.hasLayer(layer) == true ) {
					map.removeLayer(layer)
				}
			}
		})
	});''' % (str(min),str(max))
		else:
			block = make_zoom_block_filter(min,max,filter_file_dictionary)
	




	# section below is for if colorkey fields are implemented, currently not supported 
	# however this code below can be a good start maybe
	"""
	else:
		block = '''
	map.on('zoomend', function(e) {
		if ( (map.getZoom() >= %s)&&(map.getZoom() <= %s) ){ 
			if (map.hasLayer(dataLayer) != true) {
				map.addLayer(dataLayer)		
			}
		}
		else { map.removeLayer( dataLayer ) }
	})
	map.on('click',function(e) {
		var skillsSelect = document.getElementById("mapStyle");
		var selectedText2 = skillsSelect.options[skillsSelect.selectedIndex].text;
		var selectedText2 = 'COLORKEY_' + selectedText2;	
		if ( (map.getZoom() >= %s)&&(map.getZoom() <= %s)&&(selectedText2 != selectedText)){ 
				// map.addLayer(dataLayer)
			dataLayer.eachLayer(function (layer) {			
				var style = {color: layer.feature.properties[selectedText2], weight: 6, opacity: 1}
				layer.setStyle(style)
			});
		}
		else { 
			}
		var selectedText = selectedText2;
		console.log(selectedText)
	
	})''' % (str(min),str(max),str(min),str(max))
	"""
	return block

# get colorline for marker
def get_colorline_marker(color_input):
	if not 'feature.properties' in str(color_input):
		colorline="""				layer.setIcon(L.mapbox.marker.icon({'marker-color': '%s','marker-size': 'small'}))""" % get_colors(color_input)
	else:
		colorline="""				layer.setIcon(L.mapbox.marker.icon({'marker-color': %s,'marker-size': 'small'}))""" % color_input		
	return colorline

# get colorline for non-marker objects
def get_colorline_marker2(color_input):
	if not 'feature.properties' in str(color_input):
		colorline="""	    		layer.setStyle({color: '%s', weight: 3, opacity: 1});""" % get_colors(color_input)
	else:
		colorline="""	    		layer.setStyle({color: %s, weight: 6, opacity: 1});""" % color_input
	return colorline



# get colors for just markers
def get_colors(color_input):
	colors=[['light green','#36db04'],
	['blue','#1717b5'],
	['red','#fb0026'],
	['yellow','#f9fb00'],
	['light blue','#00f4fb'],
	['orange','#dd5a21'],
	['purple','#6617b5'],
	['green','#1a7e55'],
	['brown','#b56617'],
	['pink','#F08080'],
	['default','#1766B5']]
	
	# logic for if a raw color input is given 
	if '#' in color_input and len(color_input)==7:
		return color_input
	
	# logic to find the matching color with the corresponding colorkey
	for row in colors:
		if row[0]==color_input:
			return row[1]
	return '#1766B5'

	
# the function actually used to make the styles table
# headers for each geojson property parsed in here 
# html table code comes out 
def make_rows(headers):
	varblock = []
	# makes a list of rows from a given input header
	for row in headers:
		row1 = row
		row2 = row
		if row == headers[0]:
			newrow = """            var popupText = "<table><tr><th>%s: </th><td>" + feature.properties['%s']+"</td></tr>"; """ % (row1,row2)
		else:
			newrow = """            var popupText = popupText+ "<tr><th>%s: </th><td>" + feature.properties['%s']+"</td></tr>"; """ % (row1,row2)
		varblock.append(newrow)
		if row == headers[-1]:
			newrow = """            var popupText = popupText+ "<tr><th>%s: </th><td>" + feature.properties['%s']+</td></tr></table>"; """ % (row1,row2)
	return varblock


# makes the js input that will be appended into the sidebar element
def make_sidebar_string_input(headers):
	newheader = []
	for row in headers:
		if not 'colorkey' in str(row).lower():
			newheader.append(row)
	headers = newheader
	total = ''
	for row in headers:
		if not row == 'bounds':
			temp = """<b>%s: '+feature.properties['%s']+'</b><br>""" % (str(row),str(row))
		total += temp	
	total = """'<div id = "info">""" + total + "<div>'"
	return total


def get_x_axis(sizex,chartcolumns):
	delta = float(sizex) / float(len(chartcolumns))
	current = 0
	xaxis = [0]
	while not len(xaxis) == len(chartcolumns):
		current += delta
		current += 9
		xaxis.append(current)
	return xaxis 


# makes the x axis block for the graph being constructed
def make_x_axis(size,chartcolumns):
	yrange = size[1] - 25
	total = ''
	xaxisstart = '''<g transform="translate(30,0)"><g class="x axis" transform="translate(0,0)">'''
	alph = 'abcdefghijklmnopqrstuvwxyz'
	xaxis = get_x_axis(size[0],chartcolumns)
	for row,letter in itertools.izip(xaxis,alph):
		line = '''<g class="tick" transform="translate(%s,0)" style="opacity: 1;"><line y2="6" x2="0"></line><text dy=".71em" y="9" x="0" style="text-anchor: middle;">%s</text></g>''' % (row,letter.upper())
		total += line
	return xaxisstart + total

def make_y_axis(size,chartcolumns):
	yaxis = size[1]
	yaxisstart = '''<g class="y axis"><g class="tick" transform="translate(10,0)">''' 
	yaxisend = '''<g class="tick" transform="translate(0,0)" style="opacity: 1;"><line x2="-6" y2="0"></line><text dy=".32em" x="-9" y="0" style="text-anchor: end;">0%</text></g>'''
	yaxisend = yaxisend + '''<g class="tick" transform="translate(10,-270)" style="opacity: 1;"><line x2="-6" y2="0"></line><text dy=".32em" x="-9" y="0" style="text-anchor: end;">100%</text></g>'''

	return yaxisstart + yaxisend 

def make_starting_chart(size,chartcolumns):
	start = '''<svg width="%s" height="%s" id="test">''' % (size[0],size[1])
	x = make_x_axis(size,chartcolumns)
	y = make_y_axis(size,chartcolumns)
	return start + x + y

def make_chart(size,chartcolumns):
	start = make_starting_chart(size,chartcolumns)
	block = '''
	var start = '%s'
	var varlist = feature.properties['chartlist'];
	var arrayLength = varlist.length;
	var total = start;


	for (var i = 0; i < arrayLength; i++) {
		var currentstring = varlist[i];
		var line = '<rect class="bar" x="' + currentstring[0] + '" width="31" y="' + currentstring[1] + '" height="' + currentstring[2] + '" style="fill:' + currentstring[3].toString() + ';"></rect>'
		var total = total + line
	}
	$('#test').remove()
	$('#sidebar').append(total)
	''' % (start)
	return block


# makes the blocks for a sidebar string addition if needed
def make_sidebar_string(headers,chart_dictionary):
	if not chart_dictionary == False:
		chartblock = make_chart(chart_dictionary['size'],chart_dictionary['fields'])
	else: 
		chartblock = False

	stringinput = make_sidebar_string_input(headers)
	datastring = make_data_string_list(headers)
	#datastring2 = make_data_string2(headers)
	datastring2 = modify_header2(headers)
	if chartblock == False:
		block = """
				layer.on('mouseover',function(e) {
					$('#sidebar > #info').remove()
					$('#sidebar').append(%s)
					}
				);""" % (stringinput)
	else:
		block = """
		layer.on('mouseover',function(e) {
			%s
			$('#sidebar > #info').remove()
			$('#sidebar').append(%s)
			}
		);""" % (chartblock,stringinput)

	return block

# making the list that will be set as the dataset in the make_sidebar_string
def make_data_string_list(headers):
	headers = headers[10:]
	headers = headers[len(headers)/2:]
	count = 0
	total = ''
	newlist = []
	for row in headers:
		count += 1
		value = "feature.properties['%s']" % (str(row))
		newlist.append(value)
	return newlist

def modify_header2(headers):
	headers = headers[10:]
	headers = headers[len(headers)/2:]
	newheaders = []
	for row in headers:
		row = row.replace('1','')
		newheaders.append(row)
	return newheaders

# make_blockstr with color and elment options added (newer)
# wraps the appropriate table html into the javascript functions called 
def making_blockstr(varblock,count,colorline,element,zoomblock,filename,sidebarstring,colorkeyfields):
	# starting wrapper that comes before html table code
	'''
	if not colorkeyfields == False:
		start = """\n\tfunction addDataToMap%s(data, map) {\t\tvar skillsSelect = document.getElementById("mapStyle");\n\t\tvar selectedText = skillsSelect.options[skillsSelect.selectedIndex].text;\n\t\tvar selectedText = 'COLORKEY_' + selectedText\n\t\tvar dataLayer = L.geoJson(data, {\n\t\t\tonEachFeature: function(feature, layer) {""" % (count)
	else:
	'''	
	start = """\n\tfunction addDataToMap%s(data, map) {\n\t\tvar dataLayer = L.geoJson(data, {\n\t\t\tonEachFeature: function(feature, layer) {""" % (count)

    # ending wrapper that comes after html table code
	if count == 1 and colorkeyfields == False:
		end = """
		            layer.bindPopup(popupText, {autoPan:false, maxHeight:500, maxWidth:350} ); }
	        });
	    dataLayer.addTo(map);
	console.log(map.fitBounds(dataLayer.getBounds()))};\n\t};"""
	else:
		end = """
		            layer.bindPopup(popupText, {autoPan:false, maxHeight:500, maxWidth:350} ); }
	        });
	    dataLayer.addTo(map);
	\n\t};\n\t}"""


	'''
	else:
		end="""
	            layer.bindPopup(popupText, {autoPan:false, maxHeight:500, maxWidth:350} ); };
        });
    	dataLayer.addTo(map);\nconsole.log(map.fitBounds(dataLayer.getBounds()));\n\t\tsetTimeout(function() {\n\t\t\t\tdataLayer.clearLayers();\n\t\t},%s);\n\t}\n}\nsetInterval(add%s,%s)""" % (time,count,time)
	'''
	# iterates through each varblock and returns the entire bindings javascript block
	total = ''

	# logic for appending check_dropdown line to zoomblock
	if not zoomblock == '' and not colorkeyfields == False:
		pass

	# logic for replacing the datalayer add to line with the zoom text block
	if not zoomblock == '':
		end = end.replace('dataLayer.addTo(map);',zoomblock)


	for row in varblock:
		total += row

	if element == 'Point':
		return start + total + colorline + sidebarstring + end
	else:
		return start + total + '\n' + colorline + sidebarstring + end

# make bindings after color options were added
def make_bindings(headers,count,colorline,element,zoomblock,filename,sidebarstring,colorkeyfields):
	varblock = make_rows(headers)
	block = making_blockstr(varblock,count,colorline,element,zoomblock,filename,sidebarstring,colorkeyfields)	
	return block


# makes the javascript function to call and load all geojson
def async_function_call(maxcount):
	# making start block text
	start = 'function add() {\n'
	
	# makign total block that will hold text
	totalblock = start

	count = 0
	while count < maxcount:
		count +=1
		tempstring = '\tadd%s();\n' % str(count)
		totalblock += tempstring
	totalblock = totalblock + '}\nadd();'

	return totalblock


# given a list of file names and kwargs carried throughout returns a string of the function bindings for each element
def make_bindings_type(filenames,color_input,colorkey,file_dictionary,sidebar,bounds):
	# instantiating string the main string block for the javascript block of html code
	string = ''

	'''
	# logic for instantiating variable colorkey input 
	if not colorkeyfields == False:
		colorkey = 'selectedText'
	'''

	# iterating through each geojson filename
	count = 0
	for row in filenames:
		color_input = ''
		colorkeyfields = False
		count += 1
		filename = row
		zoomrange = ['','']
		# reading in geojson file into memory
		with open(filename) as data_file:    
   			data = json.load(data_file)
   		#pprint(data)

   		# getting the featuretype which will later dictate what javascript splices are needed
   		data = data['features']
   		data = data[0]
   		featuretype = data['geometry']
   		featuretype = featuretype['type']
		data = data['properties']


		# logic for overwriting colorkey fields if it exists for the filename 
		# in the file dictionary
		try:
			colorkeyfields = file_dictionary[filename][str('colorkeyfields')]
		except KeyError:
			colorkeyfields = False
		except TypeError:
			colorkeyfields = False

		if not colorkeyfields == False:
			if len(colorkeyfields) == 1:
				colorkey = colorkeyfields[0]
				colorkeyfields = False

		try:
			zoomrange = file_dictionary[filename][str('zooms')]
		except KeyError:
			zoomrange = ['','']
		except TypeError:
			zoomrange = ['','']



		# code for if the file_dictionary input isn't false 
		#(i.e. getting the color inputs out of dictionary variable)
		if file_dictionary==False and colorkey == False:			
			# logic for getting the colorline for different feature types
			# the point feature requires a different line of code
			if featuretype == 'Point':
				colorline = get_colorline_marker(color_input)
			else:
				colorline = get_colorline_marker2(color_input)



		# setting minzoom and maxzoom to be sent into js parsing 
		minzoom,maxzoom = zoomrange

		# getting filter file dictionary if filter_dictonary exists
		if not file_dictionary == False:
			filter_file_dictionary = file_dictionary[filename]
		else:
			filter_file_dictionary = False 

		# checking to see if a chart_dictionary exists
		try: 
			chart_dictionary = filter_file_dictionary['chart_dictionary']
		except KeyError:
			chart_dictionary = False
		except TypeError:
			chart_dictionary = False


		# sending min and max zoom into the function that makes the zoom block
		zoomblock = make_zoom_block(minzoom,maxzoom,count,colorkeyfields,bounds,filter_file_dictionary)

		# logic for if a color key is given 
		# HINT look here for rgb raw color integration in a color line
   		if not colorkey == '':
   			if row == filenames[0]:
   				if colorkey == 'selectedText':
   					colorkey = """feature.properties[%s]""" % colorkey
   				else:
   					colorkey = """feature.properties['%s']""" % colorkey
   			if featuretype == 'Point':
   				colorline = get_colorline_marker(str(colorkey))
   			else:
   				colorline = get_colorline_marker2(str(colorkey))


   		# this may be able to be deleted 
   		# test later 
   		# im not sure what the fuck its here for 
   		if file_dictionary == False and colorkey == '':
	   		if featuretype == 'Point':
	   			colorline = get_colorline_marker(color_input)
	   		else:
	   			colorline = get_colorline_marker2(color_input)
   		if colorkey == '' and colorkeyfields == False:
	   		if featuretype == 'Point':
	   			colorline = get_colorline_marker(color_input)
	   		else:
	   			colorline = get_colorline_marker2(color_input)

   		# iterating through each header 
   		headers = []
   		for row in data:
   			headers.append(str(row))

   		# logic for getting sidebar string that will be added in make_blockstr()
   		if sidebar == True:
   			sidebarstring = make_sidebar_string(headers,chart_dictionary)
   		else:
   			sidebarstring = ''

   		# section of javascript code dedicated to the adding the data layer 
   		if count == 1:
	   		blocky = """
	function add%s() { 
	\n\tfunction addDataToMap%s(data, map) {
	\t\tvar dataLayer = L.geoJson(data);
	\t\tvar map = L.mapbox.map('map', 'mapbox.streets',{
	\t\t\tzoom: 5
	\t\t\t}).fitBounds(dataLayer.getBounds());
	\t\tdataLayer.addTo(map)
	\t}\n""" % (count,count)
		else:
			blocky = """
	function add%s() { 
	\n\tfunction addDataToMap%s(data, map) {
	\t\tvar dataLayer = L.geoJson(data);
	\t\tdataLayer.addTo(map)
	\t}\n""" % (count,count)
		
		# making the string section that locally links the geojson file to the html document
		'''
		if not time == '':
			preloc='\tfunction add%s() {\n' % (str(count))
			loc = """\t$.getJSON('http://localhost:8000/%s',function(data) { addDataToMap%s(data,map); });""" % (filename,count)
			loc = preloc + loc
		else: 
		'''
		loc = """\t$.getJSON('http://localhost:8000/%s',function(data) { addDataToMap%s(data,map); });""" % (filename,count)			
		# creating block to be added to the total or constituent string block
		if featuretype == 'Point':
			bindings = make_bindings(headers,count,colorline,featuretype,zoomblock,filename,sidebarstring,colorkeyfields)+'\n'
			stringblock = blocky + loc + bindings
		else:
			bindings = make_bindings(headers,count,colorline,featuretype,zoomblock,filename,sidebarstring,colorkeyfields)+'\n'
			stringblock = blocky + loc + bindings
		
		# adding the stringblock (one geojson file javascript block) to the total string block
		string += stringblock

	# adding async function to end of string block
	string = string + async_function_call(count)

	return string

# makes the corresponding styled html for the map were about to load
def make_html(filenames,color_input,colorkey,apikey,file_dictionary,sidebar,bounds):
	# logic for development and fast use 
	if apikey == True:
		apikey = 'pk.eyJ1IjoibXVycGh5MjE0IiwiYSI6ImNpam5kb3puZzAwZ2l0aG01ZW1uMTRjbnoifQ.5Znb4MArp7v3Wwrn6WFE6A'

	# initial template block
	startingblock = make_startingblock(apikey,sidebar,file_dictionary)
	
	# making the bindings (i.e. the portion of the code that creates the javascript)
	bindings = make_bindings_type(filenames,color_input,colorkey,file_dictionary,sidebar,bounds)
	
	#setting the template ending block
	endingblock = """
\t\n</script>

</body>
</html>"""
	
	# creating the constituent block combining all the above portions of the html code block
	block = startingblock  + bindings + endingblock

	return block

# collection feature collecting all the geojson within the current directory
def collect():
	jsons=[]
	for dirpath, subdirs, files in os.walk(os.getcwd()):
	    for x in files:
	        if x.endswith(".geojson"):
	        	jsons.append(x)
	return jsons

# writes the html file to a document then opens it up in safari (beware it will call a terminal command)
def load(lines,filename,chrome):

	with open(filename,'w') as f:
		f.writelines(lines)

	f.close()	
	if chrome == True:
		os.system("open -a 'Google Chrome' "+'http://localhost:8000/'+filename)
	else:
		os.system("open -a Safari "+filename)


def show(url):
    return IFrame(url, width=400, height=400)


# THE FUNCTION YOU ACTUALLY USE WITH THIS MODULE
def loadparsehtml(filenames,apikey,**kwargs):
	color  = ''
	colorkey = ''
	frame = False
	file_dictionary = False
	sidebar = False
	bounds = False
	chrome = False

	# making developer option thing so that it loads url after parsed
	if apikey == True:
		frame = True


	for key,value in kwargs.iteritems():
		if key == 'color':
			color = str(value)
		if key == 'colorkey':
			colorkey = str(value)
		if key == 'frame':
			frame = value
		if key == 'file_dictionary':
			file_dictionary = value
		if key == 'sidebar':
			sidebar = value
		if key == 'bounds':
			bounds = value
		if key == 'chrome':
			chrome = value

	block = make_html(filenames,color,colorkey,apikey,file_dictionary,sidebar,bounds)
	with open('index.html','w') as f:
		f.write(block)
	f.close()	
	if frame == True:
		load(block,'index.html',chrome)
	else:
		return 'http://localhost:8000/index.html'

def a(**kwargs):
	apikey = True
	color  = ''
	colorkey = ''
	frame = True
	file_dictionary = False
	sidebar = False
	bounds = False
	chrome = False
	# making developer option thing so that it loads url after parsed
	if apikey == True:
		frame = True

	for key,value in kwargs.iteritems():
		if key == 'color':
			color = str(value)
		if key == 'colorkey':
			colorkey = str(value)
		if key == 'frame':
			frame = value
		if key == 'file_dictionary':
			file_dictionary = value
		if key == 'sidebar':
			sidebar = value
		if key == 'bounds':
			bounds = value
		if key == 'chrome':
			chrome = value


	return loadparsehtml(collect(),True,color=color,colorkey=colorkey,frame=frame,file_dictionary=file_dictionary,sidebar=sidebar,bounds=bounds,chrome=chrome)