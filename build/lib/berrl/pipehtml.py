'''
Module: pipehtml.py

A module to parse html for data in static html and for data to be updated in real time.

Created by: Bennett Murphy
email: murphy214@marshall.edu
'''

import json
import itertools
import os
from IPython.display import IFrame


# makes start block from template using 
def make_startingblock(legend,apikey):
	# makign initial template block

	# logic for if legend is empty string variable
	if not '<style>' in str(legend):
		startingblock = """
<html>
<head>
<meta charset=utf-8 />
<title>PipeGeoJSON Demo</title>
<meta name='viewport' content='initial-scale=1,maximum-scale=1,user-scalable=no' />
<script src="https://api.mapbox.com/mapbox.js/v2.2.4/mapbox.js"></script>


<script src="http://code.jquery.com/jquery-1.11.3.min.js"></script>
<link href='https://api.mapbox.com/mapbox.js/v2.2.4/mapbox.css' rel='stylesheet' />
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




<script src='https://api.mapbox.com/mapbox.js/plugins/leaflet-omnivore/v0.2.0/leaflet-omnivore.min.js'></script>

<div id='map'></div>

<script>
L.mapbox.accessToken = 'xxxxx';""".replace('xxxxx',apikey)
	else:
		startingblock = """
<html>
<head>
<meta charset=utf-8 />
<title>PipeGeoJSON Demo</title>
<meta name='viewport' content='initial-scale=1,maximum-scale=1,user-scalable=no' />
<script src="https://api.mapbox.com/mapbox.js/v2.2.4/mapbox.js"></script>


<script src="http://code.jquery.com/jquery-1.11.3.min.js"></script>
<link href='https://api.mapbox.com/mapbox.js/v2.2.4/mapbox.css' rel='stylesheet' />
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


yyyyy

<script src='https://api.mapbox.com/mapbox.js/plugins/leaflet-omnivore/v0.2.0/leaflet-omnivore.min.js'></script>

<div id='map'></div>

<script>
L.mapbox.accessToken = 'xxxxx';""".replace('xxxxx',apikey)
		# bad string concatenation to replace what will be the 
		startingblock = startingblock.replace('yyyyy',legend)

	# second string block to be concatenated to the initial block already made
	startingblock2 = """
\nvar map = L.mapbox.map('map', 'mapbox.streets',{
    zoom: 5
    });

// omnivore will AJAX-request this file behind the scenes and parse it: 

// note that there are considerations:
// - The file must either be on the same domain as the page that requests it,
//   or both the server it is requested from and the user's browser must
//   support CORS.

// Internally this uses the toGeoJSON library to decode the KML file
// into GeoJSON




\n"""
	
	# combining starting block with the second block
	startingblock = startingblock + startingblock2
	
	return startingblock

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

# make_blockstr with color and elment options added (newer)
# wraps the appropriate table html into the javascript functions called 
def making_blockstr(varblock,count,colorline,element,time):
	# starting wrapper that comes before html table code
	start = """\n\tfunction addDataToMap%s(data, map) {\n\t\tvar dataLayer = L.geoJson(data, {\n\t\t\tonEachFeature: function(feature, layer) {""" % (count)

    # ending wrapper that comes after html table code
	if time == '':
		if count == 1:
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


	else:
		end="""
	            layer.bindPopup(popupText, {autoPan:false, maxHeight:500, maxWidth:350} ); };
        });
    	dataLayer.addTo(map);\nconsole.log(map.fitBounds(dataLayer.getBounds()));\n\t\tsetTimeout(function() {\n\t\t\t\tdataLayer.clearLayers();\n\t\t},%s);\n\t}\n}\nsetInterval(add%s,%s)""" % (time,count,time)
	# iterates through each varblock and returns the entire bindings javascript block
	total = ''
	for row in varblock:
		total += row
	if element == 'Point':
		return start + total + colorline + end
	else:
		return start + total + '\n' + colorline + end

# make bindings after color options were added
def make_bindings(headers,count,colorline,element,time):
	varblock = make_rows(headers)
	block = making_blockstr(varblock,count,colorline,element,time)	
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
def make_bindings_type(filenames,color_input,colorkey,file_dictionary,time):
	# instantiating string the main string block for the javascript block of html code
	string = ''
	
	# iterating through each geojson filename
	count = 0
	for row in filenames:
		color_input = ''
		count += 1
		filename = row
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

		# code for if the file_dictionary input isn't false 
		#(i.e. getting the color inputs out of dictionary variable)
		if not file_dictionary==False:
			try:
				color_input=file_dictionary[filename]
			except Exception:
				color_input=''
			
			# logic for getting the colorline for different feature types
			# the point feature requires a different line of code
			if featuretype == 'Point':
				colorline = get_colorline_marker(color_input)
			else:
				colorline = get_colorline_marker2(color_input)

		# logic for if a color key is given 
		# HINT look here for rgb raw color integration in a color line
   		if not colorkey == '':
   			if row == filenames[0]:
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

   		# iterating through each header 
   		headers = []
   		for row in data:
   			headers.append(str(row))
   		
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
		if not time == '':
			preloc='\tfunction add%s() {\n' % (str(count))
			loc = """\t$.getJSON('http://localhost:8000/%s',function(data) { addDataToMap%s(data,map); });""" % (filename,count)
			loc = preloc + loc
		else: 
			loc = """\t$.getJSON('http://localhost:8000/%s',function(data) { addDataToMap%s(data,map); });""" % (filename,count)			
		# creating block to be added to the total or constituent string block
		if featuretype == 'Point':
			bindings = make_bindings(headers,count,colorline,featuretype,time)+'\n'
			stringblock = blocky + loc + bindings
		else:
			bindings = make_bindings(headers,count,colorline,featuretype,time)+'\n'
			stringblock = blocky + loc + bindings
		
		# adding the stringblock (one geojson file javascript block) to the total string block
		string += stringblock

	# adding async function to end of string block
	string = string + async_function_call(count)

	return string


# checks to see if a legends inputs values exist if so returns a  splice of code instantiating legend variable
def check_legend(legend):
	if legend[0]=='':
		return ''
	else:
		return 'var map2 = map.legendControl.addLegend(document.getElementById("legend").innerHTML);'

# returns the legend starting block for intially formatting the area the legend will occupy 
def make_top():
	return '''<style>
.legend label,
.legend span {
  display:block;
  float:left;
  height:15px;
  width:20%;
  text-align:center;
  font-size:9px;
  color:#808080;
  }
</style>'''

# makes the legend if variables within the create legend function indicate a legend variable was given 
def make_legend(title,colors,labels):
	colorhashs=[]
	for row in colors:
		colorhashs.append(get_colors(row))
	return '''
<div id='legend' style='display:none;'>
  <strong>%s</strong>
  <nav class='legend clearfix'>
    <span style='background:%s;'></span>
    <span style='background:%s;'></span>
    <span style='background:%s;'></span>
    <span style='background:%s;'></span>
    <span style='background:%s;'></span>
    <label>%s</label>
    <label>%s</label>
    <label>%s</label>
    <label>%s</label>
    <label>%s</label>
    <small>Source: <a href="https://github.com/murphy214/berrl">Made using Berrl</a></small>
</div>
''' % (title,colorhashs[0],colorhashs[1],colorhashs[2],colorhashs[3],colorhashs[4],labels[0],labels[1],labels[2],labels[3],labels[4])


# returns the blocks of color backgrounds for a given list of colors 
def make_colors_legend(colors):
	total = ''
	for row in colors:
		newrow = """\t<span style='background:%s;'></span>\n""" % get_colors(row)
		total += newrow
	return total

# returns the block of labelsfor a given list of label integers or floats
def make_labels_legend(labels):
	total = ''
	for row in labels:
		newrow = """\t<label>%s</label>\n""" % row
		total += newrow
	return total


# attempting to make a more dynamic legend in the same fashion as above
def make_legend2(title,colors,labels):
	start = """
<div id='legend' style='display:none;'>
  <strong>%s</strong>
  <nav class='legend clearfix'>
  """ % title

 	# code for creating color lines here 
 	colorsblock = make_colors_legend(colors)

 	# code for getting 5 labels out of any amount of labels given
 	labels = get_5labels(labels)

 	# code for creating label lines here
 	# this may also contain spacer values for every x colors to label
 	labelsblock = make_labels_legend(labels)


	end = """\t<small>Source: <a href="https://github.com/murphy214/berrl">Made using Berrl</a></small>
</div>
""" 
	total = start + colorsblock + labelsblock + end

	return total



# returns the legend starting block for intially formatting the area the legend will occupy 
def make_top2(rangelist):
	widthpercentage = 100.0 / float(len(rangelist))
	return '''<style>
.legend label,
.legend span {
  display:block;
  float:left;
  height:15px;
  width:xx%;
  text-align:center;
  font-size:9px;
  color:#808080;
  }
</style>'''.replace('xx',str(widthpercentage))



# generates 5 labels and then inserts dummy spaces in each label value not used
# may eventually accept a number of labels right now assumes 5 and returns adequate dummy labels for inbetween values
def get_5labels(rangelist):
	# getting the round value in which all labels will be rounded
	roundvalue = determine_delta_magnitude(rangelist)

	# getting newrangelist
	newrangelist = get_rounded_rangelist(rangelist,roundvalue)

	# getting maximum character size 
	maxchar = get_maxchar_range(newrangelist)

	# getting maximum width size
	if '.' in str(newrangelist[1]):
		maxwidth = get_max_width_size(maxchar,False)
	else: 
		maxwidth = get_max_width_size(maxchar,True)

	# getting the space label that occupies the maximum label size
	spacelabel = get_dummy_space_label(maxwidth)

	# getting label positions
	labelpositions = [0]
	labeldelta = len(newrangelist)/5
	currentlabelposition = 0

	# adding the 3 in between labels to the label positions list
	# this code could be modified to support a integer with the number of labels you desire
	while not len(labelpositions) == 5:
		currentlabelposition += labeldelta
		labelpositions.append(currentlabelposition)

	# iterating through the newrangelist and appending the correpsondding label based upon 
	# the above strucuture
	count = 0
	newlist = []
	for row in newrangelist:
		oldrow = row
		ind = 0
		for row in labelpositions:
			if count == row:
				ind = 1
		if ind == 1:
			if int(oldrow) == float(oldrow):
				oldrow = int(oldrow)
			newlist.append(oldrow)
		elif ind == 0:
			newlist.append(spacelabel)
		count +=1
	return newlist

# creating function the max len value of the ranges given 
def get_maxchar_range(rangelist):
	maxsize = 0
	for row in rangelist:
		size = len(str(row))
		if maxsize < size:
			maxsize = size
	return maxsize 

# gets the value that the rangelist should be rounded to 
# in attempt to maintain significant figures on the rangelist 
def determine_delta_magnitude(rangelist):
	# getting the rangedelta
	delta = rangelist[1] - rangelist[0]

	current = -15
	while 10**current < delta:
		oldcurrent = current
		current +=1

	roundvalue = oldcurrent * -1 
	return roundvalue

# returns a rangelist with the rounded to the value determined from determine_delta_magnitude
def get_rounded_rangelist(rangelist,roundvalue):
	newrangelist = []
	for row in rangelist:
		row = round(row,roundvalue)
		newrangelist.append(row)
	return newrangelist

# getting width point size from the maxchar value
def get_max_width_size(maxcharsize,intbool):
	# getting point size by adding what a period
	if intbool == False:
		pointsize = (maxcharsize - 1) * 6.673828125
		pointsize += 3.333984375
	else:
		pointsize = maxcharsize * 6.673828125
	
	return pointsize

# generates a label of only spaces to occupy the label positions 
# while avoiding overlapping with previous labels
def get_dummy_space_label(maxwidthsize):
	currentwidthsize = 0
	dummylabel = '' 
	while currentwidthsize < maxwidthsize:
		currentwidthsize += 3.333984375
		dummylabel += ' '
	return dummylabel

# creating legend instance if needed
def create_legend(title,colors,labels):
	if not title=='':
		return make_top2(colors)+'\n'+make_legend2(title,colors,labels)
	else:
		return ''

# makes the corresponding styled html for the map were about to load
def make_html(filenames,color_input,colorkey,apikey,file_dictionary,legend,time):
	# logic for development and fast use 
	if apikey == True:
		apikey = 'pk.eyJ1IjoibXVycGh5MjE0IiwiYSI6ImNpam5kb3puZzAwZ2l0aG01ZW1uMTRjbnoifQ.5Znb4MArp7v3Wwrn6WFE6A'

	# functions for creating legend block even if legend doesn't exist 
	newlegend = create_legend(legend[0],legend[1],legend[2])

	# initial template block
	startingblock = make_startingblock(newlegend,apikey)
	
	# making the bindings (i.e. the portion of the code that creates the javascript)
	bindings = make_bindings_type(filenames,color_input,colorkey,file_dictionary,time)

	# making the legend check
	checklegend = check_legend(legend)

	#setting the template ending block
	endingblock = """
\t\n</script>

</body>
</html>"""
	
	# creating the constituent block combining all the above portions of the html code block
	block = startingblock + bindings + checklegend + endingblock

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
def load(lines,filename):

	with open(filename,'w') as f:
		f.writelines(lines)

	f.close()	
	os.system('open -a Safari '+filename)


def show(url):
    return IFrame(url, width=400, height=400)

# THE FUNCTION YOU ACTUALLY USE WITH THIS MODULE
def loadparsehtml(filenames,apikey,**kwargs):
	color  = ''
	colorkey = ''
	frame = False
	file_dictionary = False
	legend = ['','','']
	time = ''


	for key,value in kwargs.iteritems():
		if key == 'color':
			color = str(value)
		if key == 'colorkey':
			colorkey = str(value)
		if key == 'frame':
			if value == True:
				frame = True
		if key == 'file_dictionary':
			file_dictionary = value
		if key == 'legend':
			legend = value
		if key == 'time':
			time = int(value)

	block = make_html(filenames,color,colorkey,apikey,file_dictionary,legend,time)
	if frame == True:
		with open('index.html','w') as f:
			f.write(block)
		f.close()
		return 'http://localhost:8000/index.html'
	else:
		load(block,'index.html')