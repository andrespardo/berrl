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
import ipywidgets as widgets
from math import floor
import numpy as np
import pandas as pd
from pipegeojson import *
from pipehtml import *
import time
from IPython.display import display
from quickmaps import *

# making html and writing html block
def make_write_html():
	block = '''
<html>
<head>
<meta charset=utf-8 />
<title>PipeGeoJSON Demo</title>
<meta name='viewport' content='initial-scale=1,maximum-scale=1,user-scalable=no' />

<script src="https://api.mapbox.com/mapbox.js/v2.2.4/mapbox.js"></script>
<script src='https://api.mapbox.com/mapbox.js/plugins/leaflet-omnivore/v0.2.0/leaflet-omnivore.min.js'></script>
<script src="http://code.jquery.com/jquery-1.11.3.min.js"></script>
<script src="sha256.js"></script>
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


<div id='map'></div>

<script src="index.js"></script>


</body>
</html>
'''
	with open ('index.html','wb') as f:
		f.write(block)


# making starting block of js file
def make_startblock(apikey):
		blockpart1 = """'use strict';\n\n/*global L */\n"""
		
		# assembling second portion of initial js string block
		blockpart2 = "L.mapbox.accessToken = '"+apikey+"';"
		

		blockpart3 = '''
		var map = L.mapbox.map('map', 'mapbox.streets',{
		    zoom: 5
		    });
		'''
		blockpart4 = '''
function check(map,dataLayer) {
	$.getJSON('http://localhost:8000/data.json',function(data) { redraw(data,map,dataLayer); });
	function redraw(data,map,dataLayer) {
		console.log(data['value'])
		if (data['value'] == true) {
			map.removeLayer(dataLayer)
			add1();
		}
		else {
			setTimeout(function() {
				check(map,dataLayer)
			},500);
			
		}
	}
}'''

		return blockpart1 + blockpart2 + blockpart3 + blockpart4 


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
		    dataLayer.addTo(map); };\n\t};"""
		else:
			end = """
			            layer.bindPopup(popupText, {autoPan:false, maxHeight:500, maxWidth:350})}})
		    dataLayer.addTo(map);
		\n\t};\n\t}"""


	else:
		if count == 1:
			end="""
				layer.bindPopup(popupText, {autoPan:false, maxHeight:500, maxWidth:350})}})\n\t\tconsole.log(map.fitBounds(dataLayer.getBounds()))\n\t\tdataLayer.addTo(map)\n\t\tcheck(map,dataLayer)\n\t}\n}\n""" 
		else:
			end="""
				layer.bindPopup(popupText, {autoPan:false, maxHeight:500, maxWidth:350})}})\n\t\tdataLayer.addTo(map)\n\t\tcheck(map,dataLayer)\n\t}\n}\n""" 
	
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
def make_bindings_type(filenames,color_input,colorkey,file_dictionary,time,portlist):
	# instantiating string the main string block for the javascript block of html code
	string = ''
	
	# iterating through each geojson filename
	count = 0
	for filename,port in itertools.izip(filenames,portlist):
		color_input = ''
		count += 1
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
   			if filename == filenames[0]:
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
		loc = """\t$.getJSON('http://localhost:%s/%s',function(data) { addDataToMap%s(data,map); });""" % (port,filename,count)
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

list = ['file.geojson']*100 

# given a number of ports and filenames 
# returns list of ports corresponding to each filename
def make_portlist(filenames,numberofports):
	delta = len(filenames) / numberofports

	count = 0 
	current = 8000
	portlist = []
	for row in filenames:
		count += 1 
		portlist.append(current)
		if count == delta:
			count = 0
			current += 1
	ports = np.unique(portlist).tolist()
	ports = pd.DataFrame(ports,columns=['PORTS'])
	ports.to_csv('ports.csv',index=False)
	return portlist


# makes the corresponding styled html for the map were about to load
def make_js(filenames,color_input,colorkey,apikey,file_dictionary,legend,time,number_ports):
	# logic for development and fast use 
	if apikey == True:
		apikey = 'pk.eyJ1IjoibXVycGh5MjE0IiwiYSI6ImNpam5kb3puZzAwZ2l0aG01ZW1uMTRjbnoifQ.5Znb4MArp7v3Wwrn6WFE6A'

	# getting port list from filenames
	portlist = make_portlist(filenames,number_ports)

	# making start block
	startblock = make_startblock(apikey)

	# functions for creating legend block even if legend doesn't exist 
	newlegend = create_legend(legend[0],legend[1],legend[2])

	
	# making the bindings (i.e. the portion of the code that creates the javascript)
	bindings = make_bindings_type(filenames,color_input,colorkey,file_dictionary,time,portlist)

	# making the legend check
	checklegend = check_legend(legend)
	
	# creating the constituent block combining all the above portions of the html code block
	block = startblock + bindings + checklegend

	# making initial data.json to load layer(s)
	# updating json object that will be hashed
	lastupdate = {'value':False}

	with open('data.json','wb') as jsonfile:
		json.dump(lastupdate,jsonfile)

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
	os.system('open -a Safari index.html')

def show(url):
    return IFrame(url, width=400, height=400)

# THE FUNCTION YOU ACTUALLY USE WITH THIS MODULE
def loadparsehtmlwidget(filenames,apikey,**kwargs):
	color  = ''
	colorkey = ''
	frame = False
	file_dictionary = False
	legend = ['','','']
	time = 5000
	test = False
	number_ports = 1

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
		if key == 'test':
			test = value
		if key == 'number_ports':
			number_ports = value

	# writing static html block 
	make_write_html()

	# getting the html block parsed from geojson dependent data
	block = make_js(filenames,color,colorkey,apikey,file_dictionary,legend,time,number_ports)
	if frame == True:
		with open('index.js','w') as f:
			f.write(block)
		f.close()
		return 'http://localhost:8000/index.html'
	elif test == True:
		print block
	else:
		load(block,'index.js')

# GOAL/IDEA
# beginning to assemble functions to assemble different widgets
# the goal being the inputs are lazy and one can input a dataset and 
# something like a dict intslider,floatslider,and a field dropdown
# as a type then a value: either a tuble min and max value or a field to querryby

# instantiates the widget for certain types of widgets
# field is the column in which the widgeet will be sliced
# type is the type of widget that it is (i.e. intslider,floatslider,dropdown thing)
# dict is an input that will be returned with an updated dictionary from the input dict
def assemble_widget_dicts(field,values,widget_type,dictlist):
	# if an empty dictionary is input for dictlist overwrites an empty list
	if dictlist == {}:
		dictlist = []

	# instantiating widget for integer slider
	if widget_type == 'IntSlider':
		minslider = widgets.IntSlider(description='Min ' + str(field),min=values[0],max=values[1],continuous_update=False)
		maxslider = widgets.IntSlider(description='Max ' + str(field),min=values[0],max=values[1],value=values[1],continuous_update=False)
		dictentry = {'type':'IntSlider','field':str(field),'widget':[minslider,maxslider]}
		dictlist.append(dictentry)
	# instantiating widget for float slider
	elif widget_type == 'FloatSlider':
		# getting significant figures of delta between min and maxx
		magnitude = determine_delta_magnitude([values[0],values[1]])
		
		# getting stepsize determined by the magnitude of difference
		# between min and max
		stepsize = 10 ** -(magnitude + 2)
		
		if stepsize < 10**-6:
			 stepsize = 10 ** -6
		minvalue = round(values[0]-(.5*stepsize),magnitude+1)
		maxvalue = round(values[1]+(.5*stepsize),magnitude+1)
		
		# setting min and max slider
		minslider = widgets.FloatSlider(description='Min ' + str(field),min=minvalue,max=maxvalue,step=stepsize,value=minvalue,continuous_update=False)
		maxslider = widgets.FloatSlider(description='Max ' + str(field),min=minvalue,max=maxvalue,step=stepsize,value=maxvalue,continuous_update=False)
		
		# adding dictentry which will be updated to the widget dictlist
		dictentry = {'type':'FloatSlider','field':str(field),'widget':[minslider,maxslider]}
		dictlist.append(dictentry)
	elif widget_type == 'Dropdown':
		# given a list of unique categorical values returns widget with dropdown
		# for each value given
		print values
		dropdownwidget = widgets.Dropdown(description=str(field), options=values)
		dropdownwidget.padding = 4

		dictentry = {'type':'Dropdown','field':str(field),'widget':dropdownwidget}
		dictlist.append(dictentry)


	return dictlist

#assemble_widget_dicts('GEOHASH',['dnvfp6g'],'Dropdown',{})




# filters rows between a range and a field
# the range can contain either a float or an int
def on_value_change(min,max):
    global data
    
    # getting header
    header = data.columns.values.tolist()
    
    new = data[(data.LAT>min)&(data.LAT<max)]

    if min < max and not len(new) == 0:
        make_points(new,list=True,filename='points.geojson')
    else:
        dummy = make_dummy(header,'points')
        parselist(dummy,'points.geojson')

'''
list range filter for integers and floats concurrency block
#int_range.observe(on_value_change, names='value')
#widgets.interact(on_value_change,min=int_range1,max=int_range2)
'''

'''
dropdownwidget  concurrency block
dropdownwidget.observe(slice_by_category, names='on_dropdown')
widgets.interact(slice_by_category,on_dropdown=uniques)
'''

def slice_by_category(on_dropdown):
    global data
    field = 'VAR23C'

    header = data.columns.values.tolist()
    new = data[data[field]==on_dropdown]
    if len(data) == 0:
        make_dummy(header,'points')
    else:
        make_points(new,list=True,filename='points.geojson')


# function that takes a list of fields and a dict list of fields and returns a list 
# dataframe of appropriate filter level
def get_df(field,fieldlist,filtereddict):
	for row in fieldlist:
		if row == field:
			return filtereddict[oldrow]
		oldrow = row

# attempting to make a function to instantiate all widgets
# it will accept a dataframe, a dictionary containing widgets
# in which it will be sliced, due to required inputs of 1 on the
# widget functions will instantiate globals and functions within the
# same function,data will be progressively filtered from its og set
# geo feature corresponding to the make_f unctions in pipegeojson
	# 'blocks'
	# 'points'
	# 'line'
	# 'polygon'
# although it will support multiple lines n
def instance_widgets(data,dictlist,ouput_filename,geo_feature_type):
	
	# instancing filename for global use
	global filename			
	global initialdata
	global filtereddict
	global dictlistglobal
	initialdata = data
	filename = ouput_filename
	count = 0
	fieldlist = []
	filtereddict = {}
	widgetslist = []
	dictlistglobal = dictlist


	# iterating through each row in dictlist (each widget)
	for row in dictlist:
		# appending row to fieldlist
		fieldlist.append(row['field'])
		#print row,count
		#raw_input('ddd')
		# instancing a global var for geo_feature_type
		global geotype
		geotype  = geo_feature_type

		widget_type = row['type']
		if widget_type == 'FloatSlider' or widget_type == 'IntSlider':
			# getting field and passing in filtereddata/fields
			# as global paramters to wrap the created fruncton
			field = row['field']
			global filtereddata
			global field
			global geotype
			global filename
			global fieldlist
			field = row['field']

			if count == 0:
				# function that takes to min and max
				# then slices df appropriately
				def on_value_change_first(min,max):
					global filtereddata
					global field
					global geotype
					global filename
					global filtereddict
					global initialdata
					global fieldlist
					

					# getting header values
					header = initialdata.columns.values.tolist()

					# slicing the df by min/max
					new = initialdata[(initialdata[field]>=min)&(initialdata[field]<=max)]
					'''
					if len(new) == 0:
						make_dummy(header,geo_feature_type)
					else:
						make_type(new,filename,geo_feature_type)
					'''
					make_dummy(header,geo_feature_type)



					lastupdate = {'value':True}

					with open('data.json','wb') as jsonfile:
						json.dump(lastupdate,jsonfile)

					time.sleep(.5)

					# updating json object that will be hashed
					lastupdate = {'value':False}


					with open('data.json','wb') as jsonfile:
						json.dump(lastupdate,jsonfile)
					
					filtereddata = new

					if len(filtereddict) == 0:
						filtereddict = {field:filtereddata}
					else:
						filtereddict[field] = filtereddata

					#if dictlistglobal[-1]['field'] == field and len(widgetslist) == len(dictlistglobal) and oldrange == 0:
					if len(widgetslist) == len(dictlistglobal):
						count = 0
						oldrow = fieldlist[0]
						# code to update slices here
						for row in fieldlist[:]:
							count += 1
							if not dictlistglobal[count-1]['type'] == 'Dropdown':
								minval,maxval = filtereddata[row].min(),filtereddata[row].max() 
								testval = tabs.children[count-1].children[0].children[1].value - tabs.children[count-1].children[0].children[0].value
								print (maxval - minval),testval
								if (maxval - minval) < testval:
									tabs.children[count-1].children[0].children[0].value = minval
									tabs.children[count-1].children[0].children[1].value = maxval
						make_type(new,filename,geo_feature_type)
	




				# getting slider 1 and slider2
				slider1,slider2 = row['widget']
				
				# instantiating widget with the desired range slices/function mapping
				on_value_change_first(initialdata[field].min(),initialdata[field].max())

				newwidget = widgets.interactive(on_value_change_first,min=slider1,max=slider2)
				newwidget = widgets.Box(children=[newwidget])
				widgetslist.append(newwidget)
			else:
				field = row['field']
				global tabs
				global oldrange
				oldrange = 0

				# function that takes to min and max
				# then slices df appropriately
				def on_value_change(min,max):
					global filtereddata
					global field
					global geotype
					global filename
					global filtereddict
					global fieldlist
					global tabs
					global oldrange

					field = fieldlist[-1]

					if not dictlistglobal[-1]['field'] == field:
						oldrange = 0


					if fieldlist[0] == field:
						filtereddata = filtereddict[field]
					else:
						#raw_input('xxx')
						filtereddata = get_df(field,fieldlist,filtereddict)
					


					# getting header value
					header = filtereddata.columns.values.tolist()

					# slicing the df by min/max
					new = filtereddata[(filtereddata[field]>=min)&(filtereddata[field]<=max)]
					
					'''
					if len(new) == 0:
						make_dummy(header,geo_feature_type)
					else:
						make_type(new,filename,geo_feature_type)
					'''
					make_dummy(header,geo_feature_type)


					lastupdate = {'value':True}

					with open('data.json','wb') as jsonfile:
						json.dump(lastupdate,jsonfile)

					time.sleep(.5)

					# updating json object that will be hashed
					lastupdate = {'value':False}


					with open('data.json','wb') as jsonfile:
						json.dump(lastupdate,jsonfile)
					
					filtereddata = new

					filtereddict[field] = filtereddata

					#if not dictlistglobal[-1]['field'] == field:
					#	oldrange = 0


					#if dictlistglobal[-1]['field'] == field and len(widgetslist) == len(dictlistglobal) and oldrange == 0:
					if len(widgetslist) == len(dictlistglobal):
						count = 0
						oldrow = fieldlist[0]
						# code to update slices here
						for row in fieldlist[:]:
							count += 1
							if not dictlistglobal[count-1]['type'] == 'Dropdown':
								minval,maxval = filtereddata[row].min(),filtereddata[row].max() 
								testval = tabs.children[count-1].children[0].children[1].value - tabs.children[count-1].children[0].children[0].value
								print (maxval - minval),testval
								if (maxval - minval) < testval:
									tabs.children[count-1].children[0].children[0].value = minval
									tabs.children[count-1].children[0].children[1].value = maxval
						make_type(new,filename,geo_feature_type)



				# getting slider 1 and slider2
				slider1,slider2 = row['widget']

				# instantiating widget with the desired range slices/function mapping
				on_value_change(initialdata[field].min(),initialdata[field].max())
				newwidget = widgets.interactive(on_value_change,min=slider1,max=slider2)
				newwidget = widgets.Box(children=[newwidget])
				widgetslist.append(newwidget)

		elif widget_type == 'Dropdown':
			global fieldcategory
			global filtereddata
			global geotype
			global filename
			global filtereddict
			global fieldlist
			fieldcategory = row['field']
			uniques = ['ALL'] + np.unique(data[fieldcategory]).tolist()


			# function that slices by category input by 
			# dropdown box within widget
			def slice_by_category(on_dropdown):
				global filtereddata
				global fieldcategory
				global geo_feature_type
				global filename
				global filtereddict
				global fieldlist

				filtereddata = get_df(fieldcategory,fieldlist,filtereddict)
				# getting header
				header = filtereddata.columns.values.tolist()

				# slicing category by appropriate field
				if not on_dropdown == 'ALL':
					new = filtereddata[filtereddata[fieldcategory]==on_dropdown]
				elif on_dropdown == 'ALL':
					new = filtereddata
				
				# updating json object that will be hashed
				lastupdate = {'value':True}


				# checking to see if data actually has values
				if len(new) == 0:
					make_dummy(header,geotype)
				else:
					make_type(new,filename,geotype)


				with open('data.json','wb') as jsonfile:
					json.dump(lastupdate,jsonfile)

				time.sleep(.5)

				# updating json object that will be hashed
				lastupdate = {'value':False}


				with open('data.json','wb') as jsonfile:
					json.dump(lastupdate,jsonfile)

				filtereddata = new

				filtereddict[fieldcategory] = filtereddata  

				print np.unique(new[fieldcategory])
			# getting drop down feature from current row in dictlist
			dropdownwidget = row['widget']

			# instantiating widget for dropdown categorical values in a field
			slice_by_category('ALL')
			dropdownwidget.observe(slice_by_category, names='on_dropdown')
			newwidget = widgets.interactive(slice_by_category,on_dropdown=uniques)
			newwidget = widgets.Box(children = [newwidget])
			widgetslist.append(newwidget)
		print count
		count += 1
	
	tabs = widgets.Tab(children=widgetslist)
	count = 0
	for row in fieldlist:
		tabs.set_title(count,row)
		count += 1
	display(tabs)
