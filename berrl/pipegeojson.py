'''
Module: pipegeojson.py

A module to convert csv, list, or dataframes files representing geospatial features  

Main Functions:
	1) make_line(data,**kwargs) - from a dataframe with lat/longs makes geojson line
	2) make_polygon(data,**kwargs) - from a dataframe with lat/longs makes geojson polygon
	3) make_blocks(data,**kwargs) - from a dataframe with lat/longs in pipegeohash syntax makes blocks
	4) make_points(data,**kwargs) - from a dataframe with lat/longs makes geojson points
	5) make_postgis_lines(data,**kwargs) - from a dataframe with with sid:4326 alignment output makes geojson LineString
	6) make_postgis_polygons(data,**kwargs) - from a dataframe with with sid:4326 alignment output makes geojson polygons

Created by: Bennett Murphy
email: murphy214@marshall.edu
'''

import json
import itertools
import pandas as pd
import numpy as np
import os
import datetime
from pipegeohash import make_geohash_blocks


#gets lat and long for polygons and lines in postgis format
def get_lat_long_align(header,extendrow,alignment_field):
	count=0
	newheader=[]
	newvalues=[]
	geometrypos=-1
	for a,b in itertools.izip(header,extendrow):
		if a=='st_asewkt' and alignment_field == False:
			geometrypos=count
		elif a=='geom':
			pass
		elif a==str(alignment_field):
			geometrypos=count
		else:
			newheader.append(a)
			newvalues.append(b)
		count+=1	
	
	# parsing through the text geometry to yield what will be rows
	try:
		geometry=extendrow[geometrypos]
		geometry=str.split(geometry,'(')
		geometry=geometry[-1]
		geometry=str.split(geometry,')')
	except TypeError:
		return [[0,0],[0,0]] 
	# adding logic for if only 2 points are given 
	if len(geometry) == 3:
		newgeometry = str.split(str(geometry[0]),',')
		
	else:
		newgeometry=geometry[:-2][0]
		newgeometry=str.split(newgeometry,',')

	coords=[]
	for row in newgeometry:
		row=str.split(row,' ')
		long=float(row[0])
		lat=float(row[1])
		coords.append([long,lat])

	return coords


#insert file name to get cordinates from
#fault tolerant attempts to look at header in first row to get lat long structure within rows
def get_cords_line(a):
	list=False
	#checking to see if the kwarg condition of inputting a list is given if so will evuate the var csvfile as if it is the list
	if list==False:
		segment=a
	else:
		segment=a
	cordblock=[]
	ind=0

	#getting header
	header=segment[0]

	#looking for lats, long and elevations within file
	#supports two points per line the most you would find for a path generally
	lats=[]
	longs=[]
	elevations=[]
	count=0
	for row in header:
		row=str(row).upper()
		if 'LAT' in str(row):
			lats.append(count)
		elif 'LONG' in str(row):
			longs.append(count)
		elif 'ELEV' in str(row):
			elevations.append(count)
		count+=1


	#if one lat and per row
	#FILETYPE OPTION: 1 LATITUDE, 1 LONGITUDE
	if len(lats)==1 and len(longs)==1 and len(elevations)==0:
		count=0
		cordrows=[]
		#getting the row numbers the latitude and longitude occur in
		rowlat1=lats[0]
		rowlong1=longs[0]

		#getting point to point rows for a flat (1 point row) csv file
		for row in segment[1:]: 
			if count==0:
				point=[row[rowlat1],row[rowlong1]]
				count=1
				newrow=point
			elif count==1:
				point=[row[rowlat1],row[rowlong1]]
				count=0
				newrow=newrow+point
				cordrows.append(newrow)

		#now going back through new list to parseinto connection points
		for row in cordrows:
			lat1=float(row[0])
			long1=float(row[1])
			lat2=float(row[2])
			long2=float(row[3])

			#making kml ready row to be appended into kml
			newrow=[long1,lat1]
			cordblock.append(newrow)
			newrow=[long2,lat2]
			cordblock.append(newrow)

	#FILETYPE OPTION: 1 LAT, 1 LONG, AND 1 ELEVATION
	elif len(lats)==1 and len(longs)==1 and len(elevations)==1:
		count=0
		cordrows=[]

		#getting the row numbers the latitude and longitude occur in
		rowlat1=lats[0]
		rowlong1=longs[0]
		rowele1=elevations[0]

		#getting point to point rows for a flat (1 point row) csv file
		for row in segment[1:]: 
			if count==0:
				point=[row[rowlat1],row[rowlong1],row[rowele1]] #lat,long,elevation
				count=1
				newrow=point
			elif count==1:
				point=[row[rowlat1],row[rowlong1],row[rowele1]] #lat,long,elevatioin
				count=0
				newrow=newrow+point
				cordrows.append(newrow)

		#now going back through new list to parseinto connection points
		for row in cordrows:
			lat1=float(row[0])
			long1=float(row[1])
			ele1=float(row[2])
			lat2=float(row[3])
			long2=float(row[4])
			ele2=float(row[5])

			newrow=[long1,lat1,ele1]
			cordblock.append(newrow)
			newrow=[long2,lat2,ele2]
			cordblock.append(newrow)

	#FILETYPE OPTION: 2 LAT, 2 LONG, AND 0 ELEVATION
	elif len(lats)==2 and len(longs)==2 and len(elevations)==0:
		count=0
		cordrows=[]

		#geting the row numbers for the lats, longs, and elevations
		rowlat1=lats[0]
		rowlong1=longs[0]
		rowlat2=lats[1]
		rowlong2=longs[1]

		for row in segment[1:]:
			lat1=row[rowlat1]
			long1=row[rowlong2]
			lat2=row[rowlat2]
			long2=row[rowlong2]

			newrow=[long1,lat1,0]
			cordblock.append(newrow)
			newrow=[long2,lat2,0]
			cordblock.append(newrow)

	#FILETYPE OPTION: 2 LAT, 2 LONG, AND 2 ELEVATIONS
	elif len(lats)==2 and len(longs)==2 and len(elevations)==2:
		count=0
		cordrows=[]

		#getting the row numbers for the lats,longs and elevations
		rowlat1=lats[0]
		rowlong1=longs[0]
		rowele1=elevations[0]
		rowlat2=lats[1]
		rowlong2=longs[1]
		rowele2=elevations[1]


		for row in segment[1:]:
			lat1=row[rowlat1]
			long1=row[rowlong1]
			ele1=row[rowele1]
			lat2=row[rowlat2]
			long2=row[rowlong2]
			ele2=row[rowele2]

			newrow=[long1,lat1,ele1]
			cordblock.append(newrow)
			newrow=[long2,lat2,ele2]
			cordblock.append(newrow)
	return cordblock


#given a csv file and any unique identifier within a row will get data to be added in a format ready to go into akml
#assumes the field name will be the corresponding title int he first (i.e. the header row)
def get_segment_info(data,postgis):
	csvfile=''
	uniqueindex=''
	list=False
	#checking to see if the kwarg condition of inputting a list is given if so will evuate the var csvfile as if it is the list
	if list==False:
		segment=data
	else:
		segment=data

	import itertools
	info=[]
	#getting segmentinfo if csv file is equal to '' and csvfile is equal to ''
	#this indictes that the segment info shouild be all likek values within the cordinate csv file
	if csvfile=='' and uniqueindex=='':
		header=segment[0]
		firstrow=segment[1]
		headerrow=[]
		lastrow=[]

		for firstval,headerval in itertools.izip(firstrow,header):
			if not postgis==True:
				lastrow.append(firstval)
				headerrow.append(headerval)
			else:
				if not 'geom' in str.lower(headerval) and not 'st_asewkt' in str.lower(headerval):
					lastrow.append(firstval)
					headerrow.append(headerval)
		header=headerrow

	else:
		#setting up generators and getting header
		header=get_header(csvfile,list)
		next_row=gen_segment(csvfile,list)
		genuniqueindex=0
		
		#while statement that iterates through generator
		while not str(uniqueindex)==str(genuniqueindex):
			segmentrow=next(next_row)
			if str(uniqueindex) in segmentrow:
				for row in segmentrow:
					if str(row)==str(uniqueindex):
						genuniqueindex=str(row)
		
		#iterating through both header info and segment info to yield a list of both
		lastrow=[]
		headerrow=[]
		for headerval,segmentval in itertools.izip(header,segmentrow):
			if not postgis==True:
				headerrow.append(headerval)
				lastrow.append(segmentval)
			else:
				if not 'geom' in str.lower(headerval) and not 'st_asewkt' in str.lower(headerval):
					headerrow.append(headerval)
					lastrow.append(segmentval)

		header=headerrow
	newrow=[]

	for row in lastrow:
		if 'NAN'in str(row).upper():
			row=str(row).upper()
		newrow.append(row)

	lastrow=newrow
	return [header,lastrow]


#from a row and a given header returns a point with a lat, elevation
def getlatlong(row,header):
	import itertools
	ind=0
	lat=''
	long=''
	for a,b in itertools.izip(row,header):
		if 'LAT' in str(b).upper():
			lat=str(a)
			ind=1
		elif 'LONG' in str(b).upper():
			long=str(a)
			ind=1
	if not lat=='' and not long=='':
		return [float(lat),float(long)]
	else:
		return [0.0,0.0]


	
#appends a list of lines to a geojson file
def parselist(list,location):
	f=open(location,'w')
	for row in list:
		f.writelines(row+'\n')
	f.close()
	print 'GeoJSON file written to location: %s' % location


# function for converting squares table to geojsonfile
def convertcsv2json(data,filename,**kwargs):
	shape=False
	strip=False
	outfilename=False
	remove_squares=False
	if kwargs is not None:
		for key,value in kwargs.iteritems():
			if key=='shape':
				if value==True:
					shape=True

	#creating a list
	newlist=[]

	#getting header
	header=data[0]

	#making the json rows
	if shape==False:
		for row in data[1:]:
			newlist.append(json.dumps(dict(zip(header,row)),indent=2))
	elif shape==True:
		newlist.append(json.dumps(dict(zip(header,data[1])),indent=2))

	#getting json filename
	if '/' in filename:
		filename=str.split(filename,'/')[1]

	newfilename=str.split(filename,'.')[0]+'.json'

	parselist(newlist,newfilename)


#given a set of table data returns the lat and longs associated with said tables
def getlatlongs(data):
	file=data

	#taking the following snippet from alignments.py
	#looking for lats, long and elevations within file
	#supports two points per line the most you would find for a path generally
	lats=[]
	longs=[]
	elevations=[]
	cordblock=[]
	count=0
	header=file[0]
	for row in header:
		row=str(row).upper()
		if 'LAT' in str(row):
			lats.append(count)
		elif 'LONG' in str(row):
			longs.append(count)
		elif 'ELEV' in str(row):
			elevations.append(count)
		count+=1


	#if one lat and per row
	#FILETYPE OPTION: 1 LATITUDE, 1 LONGITUDE
	if len(lats)==1 and len(longs)==1:
		count=0
		cordrows=[]
		#getting the row numbers the latitude and longitude occur in
		rowlat1=lats[0]
		rowlong1=longs[0]

		#getting point to point rows for a flat (1 point row) csv file
		for row in file[1:]: 
			point=[float(row[rowlat1]),float(row[rowlong1])]
			cordrows.append(point)
		return [['Lat','Long']]+cordrows
	elif len(lats)==4 and len(longs)==4:
		cordrows=[]
		cordrows2=[]
		for row in file[1:]:
			cordrows=[]
			for lat,long in itertools.izip(lats,longs):
				point=[float(row[lat]),float(row[long])]
				cordrows.append(point)
			cordrows2+=[cordrows]
		return [['Lat','Long']]+cordrows2

#given a set of data points from getlatlongs output returns north south east and west barrings to go into kml
def getextremas(data):
	points=getlatlongs(data)
	points2=points[1:]
	if len(points2)==1:
		points=pd.DataFrame(points2[0],columns=points[0])	
		south=points['Lat'].min()
		north=points['Lat'].max()
		west=points['Long'].min()
		east=points['Long'].max()
		return [east,west,south,north]
	return []


#takes a dataframe and turns it into a list
def df2list(df):
	df=[df.columns.values.tolist()]+df.values.tolist()
	return df

#returns a list with geojson in the current directory
def get_geojsons():
	jsons=[]
	for dirpath, subdirs, files in os.walk(os.getcwd(str(dirs))):
	    for x in files:
	        if x.endswith(".geojson"):
	        	jsons.append(x)
	return jsons

# collecting geojson files in a list 
def collect():
	jsons=[]
	for dirpath, subdirs, files in os.walk(os.getcwd()):
	    for x in files:
	        if x.endswith(".geojson"):
	        	jsons.append(x)
	return jsons

#cleans the current of geojson files (deletes them)
def clean_current():
	jsons=collect()	
	for row in jsons:
		os.remove(row)

#returns a list with geojson in the current directory
def get_filetype(src,filetype):
	filetypes=[]
	for dirpath, subdirs, files in os.walk(os.getcwd()+'/'+src):
	    for x in files:
	        if x.endswith('.'+str(filetype)):
	        	filetypes.append(src+'/'+x)
	return filetypes

#appends a list of lines to a geojson file
def parselist2(list,location):
	f=open(location,'w')
	for row in list:
		f.writelines(row+'\n')
	f.close()

# making all values in a partition
def fromdataframecollection(x):
	dataframe=x[0]
	featuretype=x[1]
	filename=x[2]

	if featuretype=='points':
		a=make_points(dataframe,list=True)
	elif featuretype=='lines':
		a=make_line(dataframe,list=True)
	elif featuretype=='blocks':
		a=make_blocks(dataframe,list=True)
	elif featuretype=='polygon':
		a=make_polygon(dataframe,list=True)

	parselist2(a,filename)
	return 0


#takes a list and turns it into a datafrae
def list2df(df):
    df = pd.DataFrame(df[1:], columns=df[0])
    return df

#takes a dataframe and turns it into a list
def df2list(df):
    df = [df.columns.values.tolist()]+df.values.tolist()
    return df

#function that writes csv file to memory
def writecsv(data, location):
    import csv
    with open(location, 'wb') as f:
        a = csv.writer(f, delimiter=',')
        for row in data:
                if row >= 0:
                        a.writerow(row)
                else:
                        a.writerows(row)
    print 'Wrote csv file to location: %s' % location


# concatenates two like dataframes
def concatenate_tables(table1,table2):
	header1 = table1.columns.tolist()
	header2 = table2.columns.tolist()
	frames = [table1,table2]

	if header1 == header2:
		data = pd.concat(frames)
		return data


# this function takes a dataframe table a column header, and a list objects and sets returns only rows
# containing one of the values in the list in the column header given
def querry_multiple(table,headercolumn,list):
	data=table
	dataheader = data.columns.tolist()
	data['BOOL'] = data[headercolumn].isin(list)
	data = data[data.BOOL == True]
	data = data[dataheader]
	data.columns = dataheader
	return data

# hexifies one number into two digits
# if a number is below 15 and can accounted in 1 digit 
def hexify2digit(color):
	color = hex(color)
	color = str(color)
	color = color[2:]

	# logic for if the len of color sting is only 1
	if len(color) == 1:
		color = '0'+color

	return color

# takes the color codes and turns them into a string of hex color key 
def hexify(red,green,blue):
	# red stringified
	red = hexify2digit(int(red))

	# green stringified
	green = hexify2digit(int(green))

	# blue stringified
	blue = hexify2digit(int(blue))

	return '#'+red+green+blue

# gets red green blue positions and returns the corresponding positions in eachrow
def get_rgb_positions(header):
	# getting red, green, and blue positon number
	count = 0
	for row in header:
		if row == 'RED':
			redposition = count
		elif row == 'GREEN':
			greenposition = count
		elif row == 'BLUE':
			blueposition = count
		count +=1


	return [redposition,greenposition,blueposition]

# maps a pandas table or a python containing colorkeys to corresponding color hexs
def make_colorkey_table(table):
	# logic for converting pandas dataframe to list
	if isinstance(table, pd.DataFrame):
		table = df2list(table)


	header = table[0]
	newlist = [header+['COLORKEY']]

	redposition,greenposition,blueposition = get_rgb_positions(header)


	for row in table[1:]:
		red,green,blue = row[redposition],row[greenposition],row[blueposition]
		colorkey = hexify(red,green,blue)
		newrow = row + [colorkey]
		newlist.append(newrow)

	newlist = list2df(newlist)
	
	return newlist

# the unpacking alg
def unstring_alignment(alignment_string):
	newlist = []
	alignment = str.split(alignment_string,' ')
	for row in alignment:
		long,lat = str.split(row,',')
		long,lat = float(long),float(lat)
		newlist.append([long,lat])
	return newlist

# given a list of alignments x,y syntax returns a string representation of all values
# a new implementation of string alignments will be used and shoehorned into make_polygons
# its easier to write a new one one each side then to replicate post output
def make_alignment_strings(listofalignments):
	total = []
	for row in listofalignments:
		alignment = row
		totalstring = ''
		for row in alignment:
			totalstring += str(row[0]) + ',' + str(row[1]) + ' '
		
		total.append(totalstring[:-1])

	return total

# makes a dataframe of alignments from an existing df containg each alignment info
# in desired order and a list of alignments in x,y fashion
# returns a df ready to be sent into ring geojson thing
def make_ring_table(data,listofalignments):
	# getting alignment string list
	alignment_strings = make_alignment_strings(listofalignments)

	# setting alignment field to returned list
	data['ALIGN'] = alignment_strings

	return data


#makes a geojson line from a csv file or tabular list
def make_line(csvfile,**kwargs):
	#associating attributes with a specific region
	list = True
	strip = False
	filename = False
	jsonz = False
	outfilename = False
	remove_squares = False
	postgis = False
	alignment_field = False
	bounds = False
	extrema = False
	f = False
	if kwargs is not None:
		for key,value in kwargs.iteritems():
			if key == 'strip':
				if value == True:
					strip = True
			elif key == 'list':
				if value == True:
					list = True
			elif key == 'remove_squares':
				if value == True:
					remove_squares = True
			elif key == 'outfilename':
				outfilename = str(value)
			elif key == 'filename':
				filename = str(value)
			elif key == 'postgis':
				if value == True:
					postgis = True
			elif key == 'alignment_field':
				alignment_field=value
			elif key == 'bounds':
				bounds = value
			elif key == 'extrema':
				extrema = value
			elif key == 'f':
				f = True

	# developer quick options for testing
	if f == True:
		list = True
		filename = 'holder.geojson' 

	# handling if input is a list or dataframe
	if list == True:
		data = csvfile
		csvfile = outfilename
	else:
		data = pd.read_csv(csvfile)

	#changing dataframe to list if dataframe
	if isinstance(data,pd.DataFrame):
		data = df2list(data)
	
	if postgis==True:
		coords=get_lat_long_align(data[0],data[1],alignment_field)
	else:
		count = 0
		coords = []

		for row in get_cords_line(data):
			if count==0:
				count=0
				newrow=[row[0],row[1]]
				coords.append(newrow)

	# logic for adding bounds to geojson
	if bounds == True:
		boundcords = [['LONG','LAT']] + coords
		boundcords = list2df(boundcords)
		extrema_bounds = {'n':boundcords['LAT'].max(),'s':boundcords['LAT'].min(),'e':boundcords['LONG'].max(),'w':boundcords['LONG'].min()}
		boundslist = [[extrema_bounds['w'],extrema_bounds['n']],[extrema_bounds['e'],extrema_bounds['s']]]
		boundcords = []
	
	# logic for adding bounds and extrema to geojson
	if bounds == True and not extrema == False:
		corner1 = boundslist[0]
		corner2 = boundslist[1]
		othercorner1 = [corner1[0],corner2[1]]
		othercorner2 = [corner2[0],corner1[1]]
		newboundslist = [corner1,corner2,othercorner1,othercorner2]

		# logic for checking whether bounds is within extrema
		ind = 0
		for row in newboundslist:
			if row[0] > extrema['w'] and row[0] < extrema['e'] and row[1] > extrema['s'] and row[1] < extrema['n']:
				ind = 1 
		if ind == 0:
			return False

	# getting segement infor for geojson
	z = get_segment_info(data,postgis)

	# making info dictionary
	info = dict(zip(z[0],z[1]))
	if bounds == True:
		info['bounds'] = boundslist

	#as of now witch craft that works
	c1 = ['type','geometry','properties']
	c2 = dict(zip(['type','coordinates'],['LineString',coords[:]]))

	# making e and putting into a feature list so that it can be made into a geojson
	e = dict(zip(c1,['Feature',c2,info]))
	etotal = [e]

	# making total json
	totaljson = {'type':'FeatureCollection','features':etotal}


	if not filename==False:
		with open(filename,'wb') as newgeojson:
			json.dump(totaljson,newgeojson)
		print 'Wrote %s to geojson.' % filename
	else:
		return totaljson


#makes a geojson line from a csv file or tabular list
def make_polygon(csvfile,**kwargs):
	#associating attributes with a specific region
	list = True
	strip = False
	jsonz = False
	outfilename = False
	remove_squares = False
	filename = False
	postgis = False
	alignment_field = False
	f = False
	ring = False
	bounds = False
	string_alignment = False
	if kwargs is not None:
		for key,value in kwargs.iteritems():
			if key == 'strip':
				if value == True:
					strip=True
			elif key == 'list':
				if value == True:
					list = True
			elif key == 'remove_squares':
				if value == True:
					remove_squares = True
			elif key == 'outfilename':
				outfilename=str(value)
			elif key == 'filename':
				filename = str(value)
			elif key == 'postgis':
				if value == True:
					postgis = True
			elif key == 'alignment_field':
				alignment_field = value
			elif key == 'f':
				f = True
			elif key == 'ring':
				ring = value
			elif key == 'string_alignment':
				string_alignment = value
			elif key == 'bounds':
				bounds = value

	# developer quick options for testing
	if f == True:
		list = True
		filename = 'holder.geojson' 

	# handling if input is a list or dataframe
	if list == True:
		data = csvfile
		csvfile = outfilename
	else:
		data = pd.read_csv(csvfile)

	#changing dataframe to list if dataframe
	if isinstance(data,pd.DataFrame):
		data = df2list(data)
	
	if postgis == True and string_alignment == True:
		count = 0
		for row in data[0]:
			if row == 'ALIGN':
				rowpos = count
			count += 1

		coords = unstring_alignment(data[1][rowpos])
		if bounds == True: 
			df = pd.DataFrame(coords,columns=['LONG','LAT'])
			extrema = {'w':df['LONG'].min(),'e':df['LONG'].max(),'s':df['LAT'].min(),'n':df['LAT'].max()}
			boundslist = [[extrema_bounds['w'],extrema_bounds['n']],[extrema_bounds['e'],extrema_bounds['s']]]

		data[0] = data[0][:rowpos] + data[0][rowpos+1:]
		data[1] = data[1][:rowpos] + data[1][rowpos+1:]
	elif postgis==True:
		coords=get_lat_long_align(data[0],data[1],alignment_field)
	elif string_alignment == True:
		count = 0
		for row in data[0]:
			if row == 'ALIGN':
				rowpos = count
			count += 1
		coords = unstring_alignment(data[1][rowpos])
		if not ring == False:
			ring = unstring_alignment(ring)
		
		# removing alignment string from infofields
		data1 = data[0][:rowpos] + data[rowpos:]
		data2 = data[1][:rowpos] + data[rowpos:]
		data = [data1,data2]

	else:
		count = 0
		coords = []

		for row in get_cords_line(data):
			if count==0:
				count=0
				newrow=[row[0],row[1]]
				coords.append(newrow)

	# info collection
	z = get_segment_info(data,postgis)
	# print json.dumps(dict(zip(['geometry: '],[dict(zip(['type: ','coordinates: '],['MultiLineString',[coords[:10]]]))])),indent=4)
	
	# zipping polygon info into a dictionary
	info = dict(zip(z[0],z[1]))
	if bounds == True:
		info['bounds'] = boundslist

	# as of now witch craft that works
	c1 = ['type','geometry','properties']
	if ring == False:
		c2 = dict(zip(['type','coordinates'],['Polygon', [coords]]))
	else:
		c2 = dict(zip(['type','coordinates'],['Polygon', [coords,ring]]))


	# as of now witchcraft that works
	e = dict(zip(c1,['Feature',c2,info]))
	etotal = [e]
	
	# making total json
	totaljson = {'type':'FeatureCollection','features':etotal}

	# logic for writing out to filename
	if not filename==False:
		with open(filename,'wb') as newgeojson:
			json.dump(totaljson,newgeojson)
		print 'Wrote %s to geojson.' % filename
	else:
		return totaljson

# writing a geojson implmentation thaat can have block csv files from pipegeohash directly
# see pipegeohash to get a general feel for the structure of each row in a csv file its pretty flexible mainly just requires 4 points (8 fields)
def make_blocks(csvfile,**kwargs):
	list = True
	strip = False
	outfilename = False
	remove_squares = False
	filename = False
	bounds = False
	f = False
	raw_geohashs = False
	if kwargs is not None:
		for key,value in kwargs.iteritems():
			if key == 'strip':
				if value == True:
					strip=True
			elif key == 'list':
				if value == True:
					list=True
			elif key == 'remove_squares':
				if value == True:
					remove_squares=True
			elif key == 'outfilename':
				outfilename=value
			elif key == 'filename':
				filename = str(value)
			elif key == 'bounds':
				bounds = value
			elif key == 'f':
				f = True
			elif key == 'raw_geohashs':
				raw_geohashs = value

	# logic for converting raw geohash list into
	# a block dataframe
	if not raw_geohashs == False:
		csvfile = make_geohash_blocks(csvfile)

	# developer quick options for testing
	if f == True:
		list = True
		filename = 'holder.geojson' 

	# handling if input is a list or dataframe
	if list == True:
		data = csvfile
		csvfile = outfilename
	else:
		data = pd.read_csv(csvfile)

	#changing dataframe to list if dataframe
	if isinstance(data,pd.DataFrame):
		data = df2list(data)

	#getting header
	header = data[0]

	# getting cord positons for each lat and long
	count = 0
	copos = []
	for row in header:
		if 'LAT' in row or 'LONG' in row:
			if not row[-1] == 'T' and not row[-1] == 'G':
				copos.append(count)
		count += 1
	coposbounds = [copos[0],copos[-1]]

	# checking to see if a header and row value needs to 
	# be refactored for stripping out unneeded properties
	newheader = []
	if strip == True:
		count = 0
		for row in header:
			if 'COLORKEY' in row:
				newheader.append(row)
				rowpos = count
			count += 1
	else:
		newheader = header

	# getting new header after factoring out cord positions
	newheader = newheader[:coposbounds[0]] + newheader[coposbounds[1]+1:]
	etotal = []

	for row in data[1:]:
		#now extrecting the point corners back out to be passed into a geojson file
		#I realize this is silly 
		lats = [row[copos[0]],row[copos[2]],row[copos[4]],row[copos[6]]]
		longs = [row[copos[1]],row[copos[3]],row[copos[5]],row[copos[7]]]
		extrema = [min(longs),max(longs),min(lats),max(lats)]

		# assembling points from extrema
		point1 = [extrema[0],extrema[-1]] # top left
		point2 = [extrema[1],extrema[-1]]
		point3 = [extrema[1],extrema[-2]] # bottom right
		point4 = [extrema[0],extrema[-2]]

		#getting the cords list object from each corner point
		coords = [[point1,point2,point3,point4,point1]]


		# getting the new row if strip is equal to true
		if strip == True:
			row = [row[rowpos]]

		row = row[:coposbounds[0]] + row[coposbounds[1]+1:]

		# logic for adding bounds to row value will attempt a straight list
		# integration with properties not sure if its in spec
		if bounds == True:
			boundslist = [point1,point3]		
			newheader = newheader + ['bounds']
			row = row + [boundslist]

		#getting info or properties
		info = dict(zip(newheader,row))

		#using the same shit tier code that works I did before (this will be fixed)
		#as of now witch craft that works
		c1=['type','geometry','properties']
		c2=dict(zip(['type','coordinates'],['Polygon',coords]))

		# new e that adds what it needs to 
		e = dict(zip(c1,['Feature',c2,info]))
		
		# adding e to e total		
		etotal.append(e)

	# making total json 
	totaljson = {'type':'FeatureCollection','features':etotal}


	# logic for writing out to a filename
	if not filename==False:
		with open(filename,'wb') as newgeojson:
			json.dump(totaljson,newgeojson)
		print 'Wrote %s to geojson.' % filename

	else:
		return totaljson


#makes a point geojson file
def make_points(csvfile,**kwargs):
	list = True
	strip = False
	outfilename = False
	filename = False
	remove_squares = False
	bounds = False
	f = False
	if kwargs is not None:
		for key,value in kwargs.iteritems():
			if key == 'strip':
				if value == True:
					strip = True
			elif key == 'list':
				if value == True:
					list = True
			elif key == 'remove_squares':
				if value == True:
					remove_squares = True
			elif key == 'outfilename':
				outfilename = str(value)
			elif key == 'filename':
				filename = str(value)
			elif key == 'bounds':
				bounds = value
			elif key == 'f':
				f = True

	# developer quick options for testing
	if f == True:
		list = True
		filename = 'holder.geojson' 

	# handling if input is a list or dataframe
	if list == True:
		data = csvfile
		csvfile = outfilename
	else:
		data = pd.read_csv(csvfile)

	#changing dataframe to list if dataframe
	if isinstance(data,pd.DataFrame):
		data = df2list(data)


	total=[]
	header=data[0]
	row1 = data[1]
	latpos = 0
	longpos = 0 
	count = 0
	# getting the lat and row positions for each row
	for a,b in itertools.izip(row1,header):
		if 'LAT' in str(b).upper():
			latpos = count
			ind=1
		elif 'LONG' in str(b).upper():
			longpos = count
			ind=1
		count += 1

	# creating list for etotal
	etotal = []
	for row in data[1:]:
		#iterating through each point in file
		longandlat=[row[longpos],row[latpos]]
		if not str(longandlat[0]).upper()=='NAN' and not str(longandlat[1]).upper()=='NAN':

			oldrow=row
			newrow=[]
			for row in oldrow:
				if 'NAN'in str(row).upper():
					row=str(row).upper()
				newrow.append(row)
			oldrow=newrow


			#zipping the header and row
			info = dict(zip(header,oldrow))

			# logic for adding point to the properties field
			if bounds == True:
				info['bounds'] = longandlat

			#as of now witch craft that works
			c1 = ['type','geometry','properties']
			c2 = dict(zip(['type','coordinates'],['Point',longandlat]))

			#as of now witchcraft that works
			e = dict(zip(c1,['Feature',c2,info]))

			#enew = {'type':'Feature'}
			etotal.append(e)


	#print etotal
	totaljson = {'type':'FeatureCollection','features':etotal}

	# logic for writing to filename if given
	if not filename==False:
		with open(filename,'wb') as newgeojson:
			json.dump(totaljson,newgeojson)
		print 'Wrote %s to geojson.' % filename
	else:
		return totaljson

# makes lines for a postgis database
def make_postgis_lines(table,filename,**kwargs):
	alignment_field = False
	spark_output = False
	bounds = False
	if kwargs is not None:
		for key,value in kwargs.iteritems():
			if key == 'alignment_field':
				alignment_field = value 
			if key == 'spark_output':
				spark_output = value
			if key == 'bounds':
				bounds = value

	#changing dataframe to list if dataframe
	if isinstance(table,pd.DataFrame):
		table=df2list(table)
	header=table[0]

	total = []
	# making table the proper iterable for each input 
	if spark_output == True:
		# list for adding feature collection headerr
		table = sum(table,[])
	else:
		table = table[1:]


	count=0
	total=0
	for row in table:
		count+=1
		# logic to treat rows as outputs of make_line or to perform make_line operation
		if spark_output == False:
			value = make_line([header,row],list=True,postgis=True,alignment_field=alignment_field,bounds=bounds)
		elif spark_output == True:
			value = row

		# logic for how to handle starting and ending geojson objects
		if row==table[0]:
			#value=make_line([header,row],list=True,postgis=True,alignment_field=alignment_field)
			if not len(table)==2:
				totalvalue=value
		else:
			totalvalue['features'].append(value['features'][0])
	
	#parselist(totalvalue,filename)
	with open(filename,'wb') as newgeojson:
		json.dump(totalvalue,newgeojson)
	print 'Wrote %s to geojson.' % filename


# makes polygons for a postgis database
def make_postgis_polygons(table,filename,**kwargs):
	string_alignment = False
	bounds = False
	for key,value in kwargs.iteritems():
		if key == 'string_alignment':
			string_alignment = value
		if key == 'bounds':
			boundry = value
	# changing dataframe to list if dataframe
	# still needs some work
	if isinstance(table,pd.DataFrame):
		table=df2list(table)
	header=table[0]

	count=0
	for row in table[1:]:
		count+=1
		if row==table[1]:
			value=make_polygon([header,row],list=True,postgis=True,string_alignment=string_alignment,bounds=bounds)
			totalvalue = value

		else:
			value=make_polygon([header,row],list=True,postgis=True,string_alignment=string_alignment,bounds=bounds)
			
			totalvalue['features'].append(value['features'][0])
	
	#parselist(totalvalue,filename)
	with open(filename,'wb') as newgeojson:
		json.dump(totalvalue,newgeojson)
	print 'Wrote %s to geojson.' % filename

# given a ring table writes geojson to file with structure indicated
def make_tiered_polygon(ringtable,filename):
	# getting header
	header = ringtable.columns.values.tolist()
	
	count = 0
	# getting row position of alignment field
	for row in header:
		if row == 'ALIGN':
			rowpos = count
		count += 1

	count = 0
	count2 = 0
	for row in ringtable.values.tolist():
		if count == 0:
			count = 1
		else:
			if count2 == 0:
				count2 = 1
				totalvalue = make_polygon([header,oldrow],string_alignment=True,ring=row[rowpos])
			else:
				value = make_polygon([header,oldrow],string_alignment=True,ring=row[rowpos])
				totalvalue['features'].append(value['features'][0])
		oldrow = row

	# appending last independent ring to set
	value = make_polygon([header,row],string_alignment=True)
	totalvalue['features'].append(value['features'][0])

	# writing file out
	with open(filename,'wb') as newgeojson:
		json.dump(totalvalue,newgeojson)
	print 'Wrote %s to geojson.' % filename
			