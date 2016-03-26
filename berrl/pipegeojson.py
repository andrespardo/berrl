'''
Module: pipegeojson.py

A module to convert csv, list, or dataframes files representing geospatial features  

Created by: Bennett Murphy
email: murphy214@marshall.edu
'''

import json
import itertools
import geohash
import pandas as pd
import numpy as np
import os
from IPython.display import IFrame

#function that reads csv file to memory
def read(file):
	import csv
	data=[]
	f=csv.reader(open(file,'rb'),delimiter=',',quotechar="\"")
	for row in f:
		data.append(row)
	return data


#gets lat and long for polygons and lines in postgis format
def get_lat_long_align(header,extendrow):
	count=0
	newheader=[]
	newvalues=[]
	for a,b in itertools.izip(header,extendrow):
		if a=='st_asewkt':
			geometrypos=count
		elif a=='geom':
			pass
		else:
			newheader.append(a)
			newvalues.append(b)
		count+=1	
	
	# parsing through the text geometry to yield what will be rows
	geometry=extendrow[geometrypos]
	geometry=str.split(geometry,'(')
	geometry=geometry[-1]
	geometry=str.split(geometry,')')
	geometry=geometry[:-2][0]
	geometry=str.split(geometry,',')

	coords=[]

	for row in geometry:
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


#makes a geojson line from a csv file or tabular list
def make_line(csvfile,**kwargs):
	#associating attributes with a specific region
	list=False
	strip=False
	filename=False
	jsonz=False
	outfilename=False
	remove_squares=False
	postgis=False
	if kwargs is not None:
		for key,value in kwargs.iteritems():
			if key=='strip':
				if value==True:
					strip=True
			elif key=='list':
				if value==True:
					list=True
			elif key=='remove_squares':
				if value==True:
					remove_squares=True
			elif key=='outfilename':
				outfilename=str(value)
			elif key=='filename':
				filename=str(value)
			elif key=='postgis':
				if value==True:
					postgis=True

	# handling if input is a list or dataframe
	if list==True:
		a=csvfile
		csvfile=outfilename
	else:
		a=read(csvfile)

	#changing dataframe to list if dataframe
	if isinstance(a,pd.DataFrame):
		a=df2list(a)
	
	if postgis==True:
		coords=get_lat_long_align(a[0],a[1])
	else:
		count=0
		coords=[]

		for row in get_cords_line(a):
			if count==0:
				count=0
				newrow=[row[0],row[1]]
				coords.append(newrow)


	z=get_segment_info(a,postgis)
	#print json.dumps(dict(zip(['geometry: '],[dict(zip(['type: ','coordinates: '],['MultiLineString',[coords[:10]]]))])),indent=4)


	#getting properties
	a1=dict(zip(['properties'],['']))
	a2=dict(zip(z[0],z[1]))
	a3=dict(zip(['properties'],[a2]))


	#as of now witch craft that works
	c1=['geometry','properties']
	c2=dict(zip(['type','coordinates'],['LineString',coords[:]]))
	b=dict(zip(['geometry'],[dict(zip(['type','coordinates'],['LineString',coords[:]]))]))
	c=dict(zip(['type'],['Feature']))
	f=dict(zip(['type'],['FeatureCollection']))

	#as of now witchcraft that works
	e=dict(zip(c1,[c2,a2]))
	new=json.dumps(c,indent=7)[:-1]+json.dumps(e,indent=7)[2:]
	beg=['{ "type": "FeatureCollection",',
    '\t"features": [','  {  "type": "Feature",']
	gf=beg+[new[27:-1]]+['\t}','\t]']+[new[-1:]]

	if not filename==False:
		parselist(gf,filename)
	else:
		return gf


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
		#this querries and parses the data for a 'location' string in the value position (i.e. lat and long with syntax '(lat, long)' or 'lat, long')
		'''
		elif 'LOCATION' in str(b).upper() and ind==0:
			val=str.split(str(a),',')
			if '(' in str(a) and ')' in str(a) and len(val)>2:
				lat=str(val[0])
				lat=lat[1:]
				long=str(val[1])
				long=long[1:-1]
			else:
				if len(val)==2:
					lat=str(val[0])
					long=str(val[1])
					if long[0]==' ':
						long=long[1:]
				else:
					lat=0
					long=0
					print lat,long
			'''
	if not lat=='' and not long=='':
		return [float(lat),float(long)]
	else:
		return [0.0,0.0]


#makes a point geojson file
def make_points(csvfile,**kwargs):
	list=False
	strip=False
	outfilename=False
	filename=False
	remove_squares=False
	jsonz=True
	if kwargs is not None:
		for key,value in kwargs.iteritems():
			if key=='strip':
				if value==True:
					strip=True
			elif key=='list':
				if value==True:
					list=True
			elif key=='remove_squares':
				if value==True:
					remove_squares=True
			elif key=='outfilename':
				outfilename=str(value)
			elif key=='jsonz':
				if value==True:
					jsonz=True
			elif key=='filename':
				filename=str(value)

	#checking for dataframe input
	if list==True:
		a=csvfile
	else:
		a=read(csvfile)

	#changing dataframe to list if dataframe
	if isinstance(a,pd.DataFrame):
		a=df2list(a)

	data=a
	total=[]
	header=data[0]
	for row in data[1:]:
		#iterating through each point in file
		latandlong=getlatlong(row,header)
		longandlat=[latandlong[1],latandlong[0]]
		if not str(longandlat[0]).upper()=='NAN' and not str(longandlat[1]).upper()=='NAN':

			oldrow=row
			newrow=[]
			for row in oldrow:
				if 'NAN'in str(row).upper():
					row=str(row).upper()
				newrow.append(row)
			oldrow=newrow


			#zipping the header and row
			info=dict(zip(header,oldrow))

			start=['{ "type": "FeatureCollection",','\t"features": [']

			#getting properties
			a1=dict(zip(['properties'],['']))
			a3=dict(zip(['properties'],[info]))


			#as of now witch craft that works
			c1=['geometry','properties']
			c2=dict(zip(['type','coordinates'],['Point',longandlat]))
			b=dict(zip(['geometry'],[dict(zip(['type','coordinates'],['LineString',longandlat]))]))
			c=dict(zip(['type'],['Feature']))
			f=dict(zip(['type'],['FeatureCollection']))

			#as of now witchcraft that works
			e=dict(zip(c1,[c2,info]))
			new=json.dumps(c,indent=7)[:-1]+json.dumps(e,indent=7)[2:]
			new=str.split(new,'\n')
			new=['\t{ "type": "Feature",']+new[2:-1]+['\t},']
			total+=new

	# adding finishing lines
	readytowrite=start+total[:-1]+['\t}','\t]','}']

	# logic for writing to filename if given
	if not filename==False:
		parselist(readytowrite,filename)
	else:
		return readytowrite
	
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

# writing a geojson implmentation thaat can have block csv files from pipegeohash directly
# see pipegeohash to get a general feel for the structure of each row in a csv file its pretty flexible mainly just requires 4 points (8 fields)
def make_blocks(csvfile,**kwargs):
	list=False
	strip=False
	outfilename=False
	remove_squares=False
	filename=False
	if kwargs is not None:
		for key,value in kwargs.iteritems():
			if key=='strip':
				if value==True:
					strip=True
			elif key=='list':
				if value==True:
					list=True
			elif key=='remove_squares':
				if value==True:
					remove_squares=True
			elif key=='outfilename':
				outfilename=value
			elif key=='filename':
				filename=str(value)

	#checking for dataframe input
	if list==True:
		a=csvfile
		csvfile=outfilename
	else:
		#if list is equal to false reading the defualt assumed csvfile location
		a=read(csvfile)

	#changing dataframe to list if dataframe
	if isinstance(a,pd.DataFrame):
		a=df2list(a)


	start=['{ "type": "FeatureCollection",','\t"features": [']
	total=[]

	#getting header
	header=a[0]
	for row in a[1:]:
		#getting extremas
		extrema=getextremas([header,row])

		#now extrecting the point corners back out to be passed into a geojson file
		#I realize this is silly 
		point1=[extrema[0],extrema[-1]]
		point2=[extrema[1],extrema[-1]]
		point3=[extrema[1],extrema[-2]]
		point4=[extrema[0],extrema[-2]]

		#getting the cords list object from each corner point
		coords=[[point1,point2,point3,point4,point1]]

		#getting info or properties
		info=dict(zip(header,row))
		
		#using the same shit tier code that works I did before (this will be fixed)
		#as of now witch craft that works
		c1=['geometry','properties']
		c2=dict(zip(['type','coordinates'],['Polygon',coords]))
		b=dict(zip(['geometry'],[dict(zip(['type','coordinates'],['LineString',coords]))]))
		c=dict(zip(['type'],['Feature']))
		f=dict(zip(['type'],['FeatureCollection']))

		#as of now witchcraft that works
		e=dict(zip(c1,[c2,info]))
		new=json.dumps(c,indent=7)[:-1]+json.dumps(e,indent=7)[2:]
		new=str.split(new,'\n')
		new=['\t{ "type": "Feature",']+new[2:-1]+['\t},']
		total+=new

	# adding finishing syntax to geojson
	readytowrite=start+total[:-1]+['\t}','\t]','}']

	# logic for writing out to a filename
	if not filename==False:
		parselist(readytowrite,filename)
	else:
		return readytowrite


#makes a geojson line from a csv file or tabular list
def make_polygon(csvfile,**kwargs):
	#associating attributes with a specific region
	list=False
	strip=False
	jsonz=False
	outfilename=False
	remove_squares=False
	filename=False
	postgis=False
	if kwargs is not None:
		for key,value in kwargs.iteritems():
			if key=='strip':
				if value==True:
					strip=True
			elif key=='list':
				if value==True:
					list=True
			elif key=='remove_squares':
				if value==True:
					remove_squares=True
			elif key=='outfilename':
				outfilename=str(value)
			elif key=='filename':
				filename=str(value)
			elif key=='postgis':
				if value==True:
					postgis=True

	# logic for if it is a csv file or list/dataframe
	if list==True:
		a=csvfile
		csvfile=outfilename
	else:
		a=read(csvfile)

	#changing dataframe to list if dataframe
	if isinstance(a,pd.DataFrame):
		a=df2list(a)
	
	# coordinate collection 
	if postgis==True:
		coords=get_lat_long_align(a[0],a[1])
	else:
		count=0
		coords=[]

		for row in get_cords_line(a):
			if count==0:
				count=0
				newrow=[row[0],row[1]]
				coords.append(newrow)

	# info collection
	z=get_segment_info(a,postgis)
	# print json.dumps(dict(zip(['geometry: '],[dict(zip(['type: ','coordinates: '],['MultiLineString',[coords[:10]]]))])),indent=4)


	# getting properties
	a1=dict(zip(['properties'],['']))
	a2=dict(zip(z[0],z[1]))
	a3=dict(zip(['properties'],[a2]))

	# as of now witch craft that works
	c1=['geometry','properties']
	c2=dict(zip(['type','coordinates'],['Polygon', [coords]]))
	c=dict(zip(['type'],['Feature']))
	f=dict(zip(['type'],['FeatureCollection']))

	# as of now witchcraft that works
	e=dict(zip(c1,[c2,a2]))
	new=json.dumps(c,indent=7)[:-1]+json.dumps(e,indent=7)[2:]
	beg=['{ "type": "FeatureCollection",',
    '\t"features": [','  {  "type": "Feature",']
	
	# adding finishing lines to geojson
	gf=beg+[new[27:-1]]+['\t}','\t]']+[new[-1:]]

	# logic for writing out to filename
	if not filename==False:
		parselist(gf,filename)
	else:
		return gf

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

def show(url):
	return IFrame(url, width=1000, height=600)

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

# makes lines for a postgis database
def make_postgis_lines(table,filename,**kwargs):
	#changing dataframe to list if dataframe
	if isinstance(table,pd.DataFrame):
		table=df2list(table)
	header=table[0]

	count=0
	for row in table[1:]:
		count+=1
		try:
			if row==table[1]:
				value=make_line([header,row],list=True,postgis=True)
				if not len(table)==2:
					value=value[:-3]
					totalvalue=value+['\t},']
			
			elif row==table[-1]:
				value=make_line([header,row],list=True,postgis=True)
				value=value[2:]
				totalvalue=totalvalue+value
			else:
				value=make_line([header,row],list=True,postgis=True)
				value=value[2:-3]
				value=value+['\t},']
				totalvalue=totalvalue+value
		except Exception:
			print 'pass'

	parselist(totalvalue,filename)

# makes polygons for a postgis database
def make_postgis_polygons(table,filename,**kwargs):
	# changing dataframe to list if dataframe
	# still needs some work
	if isinstance(table,pd.DataFrame):
		table=df2list(table)
	header=table[0]

	count=0
	for row in table[1:]:
		count+=1
		if row==table[1]:
			value=make_polygon([header,row],list=True,postgis=True)
			value=value[:-3]
			totalvalue=value+['\t},']
		elif row==table[-1]:
			value=make_polygon([header,row],list=True,postgis=True)
			value=value[2:]
			totalvalue=totalvalue+value
		else:
			value=make_polygon([header,row],list=True,postgis=True)
			value=value[2:-3]
			value=value+['\t},']
			totalvalue=totalvalue+value
	parselist(totalvalue,filename)

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

# extends a new table down from a post gis row and header
def extend_geohashed_table(header,extendrow,precision,**kwargs):
	count=0
	newheader=[]
	newvalues=[]
	return_dataframe = False
	for key,value in kwargs.iteritems():
		if key == 'return_dataframe':
			if value == True:
				return_dataframe = True


	for a,b in itertools.izip(header,extendrow):
		if a=='st_asewkt':
			geometrypos=count
		elif a=='geom':
			pass
		else:
			newheader.append(a)
			newvalues.append(b)
		count+=1

	# adding values to newheader that were in the text geometry
	newheader=newheader+['LAT','LONG','DISTANCE','GEOHASH']
	
	# parsing through the text geometry to yield what will be rows
	try: 
		geometry=extendrow[geometrypos]
		geometry=str.split(geometry,'(')
		geometry=geometry[-1]
		geometry=str.split(geometry,')')
		geometry=geometry[:-2][0]
		geometry=str.split(geometry,',')


		# setting up new table that will be returned as a dataframe
		newtable=[newheader]
		for row in geometry:
			row=str.split(row,' ')
			distance=float(row[-1])
			lat=float(row[1])
			long=float(row[0])
			try: 
				hash = geohash.encode(float(lat), float(long), precision)
				newrow=newvalues+[lat,long,distance,hash]
				newtable.append(newrow)
			except Exception:
				pass

	except Exception:
		newtable=[['GEOHASH'],['']]

	# taking table from list to dataframe
	newtable=list2df(newtable)

	if return_dataframe == True:
		return newtable
	return np.unique(newtable['GEOHASH']).tolist()

# returning dictionary with a unique identifier and geohashed squares occuring on line vector data
def make_line_dict(table,precision,position):
	# where table is dataframe table
	# where precision is the precision of the geohash
	# where position is the unique identifier dictioniary integer positon in each row 
	# return dict entry for each line segment {identifier:[geohash list]}
	data=table

	if isinstance(data,pd.DataFrame):
		data=df2list(data)
	header=data[0]

	count=0
	for row in data[1:]:
		temp=extend_geohashed_table(header,row,precision)
		uniques=np.unique(temp['GEOHASH']).tolist()
		if count==0:
			count=1
			uniquedict={row[position]:uniques}
		else:
			uniquedict[row[position]]=uniques
	return uniquedict

# returning DataFrame with ever geohashed square and every routeid with each one
def make_line_frame(table,precision,position,**kwargs):
	# where table is dataframe table
	# where precision is the precision of the geohash
	# where position is the unique identifier dictioniary integer positon in each row 
	# return dict entry for each line segment {identifier:[geohash list]}
	# csv is a bool that returns a csv file or tries to read a csv file if one is available if not it will create and write one
	csv = False
	data=table
	if kwargs is not None:
		for key,value in kwargs.iteritems():
			if key == 'csv':
				if value == True:
					csv = True

	# doing dataframe logic
	if isinstance(data,pd.DataFrame):
		data=df2list(data)
	header=data[0]
	columnheader = header[position]
	newtable = [['GEOHASH',columnheader]]

	count=0
	count2=0
	total=0

	if csv == True:
		try: 
			newtable = pd.read_csv('line_frame'+str(precision)+'.csv')
			return newtable
		except Exception:
			print 'No line frame csv file found, creating line frame.'
	for row in data[1:]:
		count2+=1
		uniques = extend_geohashed_table(header,row,precision)
		temptable = ['GEOHASH']+uniques
		temptable = pd.DataFrame(temptable[1:], columns=[temptable[0]])
		temptable[columnheader] = row[position]
		temptable = df2list(temptable)
		newtable += temptable[1:]
		if count2 == 1000:
			total+=count2
			count2=0
			print '[%s/%s]' % (total,len(data))

	if csv == True:
		writecsv(newtable,'line_frame'+str(precision)+'.csv')

	return list2df(newtable)

# generator for a line dictionary 
def gen_linedict_keys(linedict):
	for row in linedict.keys():
		yield row

# from a line dictionary like the one created above returns the first instance of a geohash being found within 
# any of the dictionary entries
def get_uniqueid_linedict(linedict,geohash):
	nextkey=gen_linedict_keys(linedict)
	found=False
	while found==False:
		try: 
			key=next(nextkey)
			linedictlist=linedict[key]
			for row in linedictlist:
				if row==geohash:
					found=True
					uniqueid=key
					return uniqueid
		except Exception:
			return ''

# concatenates two like dataframes
def concatenate_tables(table1,table2):
	header1 = table1.columns.tolist()
	header2 = table2.columns.tolist()
	frames = [table1,table2]

	if header1 == header2:
		data = pd.concat(frames)
		return data


# bind a geohashed table of occurances to vector data by unique column input
def bind_geohashed_data_dict(uniqueid,linedict,geohashed_table,vector_database):
	data = vector_database
	# iterating through each traffic fatility and getting route
	total = [[uniqueid,'COUNT']]
	uniques=[]
	for row in df2list(geohashed_table)[1:]:
		hash = row[-1]
		unique = get_uniqueid_linedict(linedict,hash)
		total.append([unique,1])
		uniques.append(unique)

	total = list2df(total)

	uniques = np.unique(uniques).tolist()
	# taking away null values returned 
	if uniques[0] == '':
		uniques = uniques[1:]

	total = total.groupby([uniqueid],sort=True).sum()
	total = total.reset_index()
	total = df2list(total)

	count=0
	for row in total[1:]:
		if count == 0:
			totaldict = {row[0]:row[1]}
			count=1
		else: 
			totaldict[row[0]] = row[1]

	# taking total and creating a new dataframe from uniqueids present
	total = total[1:]
	dataheader = data.columns.tolist()
	data['BOOL'] = data[uniqueid].isin(uniques)
	data = data[data.BOOL == True]
	data = data[dataheader]
	data = df2list(data)

	# setting up header
	newdata=[data[0] + ['COUNT']]

	# getting uniqueid positon number
	count=0
	for row in data[0]:
		if row == uniqueid:
			position=count
		count+=1

	# iterating through data
	for row in data[1:]:
		print row
		key = row[position]
		value = totaldict[key]
		newrow = row + [value]
		newdata.append(newrow)

	# taking back to df
	newdata = list2df(newdata)

	return newdata

# given a unique column id (column header), a lineframe, and geohashed_data, and a vector database
# returns a dataframe of aggregated linesegments by count of occurence from geohashed data
def bind_geohashed_data_frame(uniqueid,lineframe,geohashed_data,vector_database):
	data = vector_database

	# getting unique geohashs
	uniques = np.unique(geohashed_data['GEOHASH']).tolist()

	# creating a dataframe with only applicable geohashs to get uniqueids found
	newdata = querry_multiple(lineframe,'GEOHASH',uniques)

	# grouping by routeid and then creating a dictionary 
	newdata['COUNT'] = 1 
	groupeddata = newdata[[uniqueid,'COUNT']]
	groupeddata = groupeddata.groupby([uniqueid],sort=True).sum()
	groupeddata = groupeddata.reset_index()
	uniqueids = np.unique(groupeddata[uniqueid]).tolist()
	groupeddata = df2list(groupeddata[[uniqueid,'COUNT']])

	# creating a dictionary of grouped data to use the keys to create
	count=0
	for row in groupeddata[1:]:
		if count == 0:
			totaldict = {str(row[0]):row[1]}
			count=1
		else: 
			totaldict[str(row[0])] = row[1]

	newunique=[]
	for row in uniqueids:
		newunique.append(str(row))
	uniqueids=newunique

	# creating dataframe of vector data using only routeids found
	specificdata = querry_multiple(data,uniqueid,uniqueids)

	# getting header and adding "COUNT" value
	header = specificdata.columns.tolist() + ['COUNT']

	# setting up newtable from header
	newtable = [header]

	# getting uniqueid positon number
	data = df2list(data)
	count=0
	for row in data[0]:
		if row == uniqueid:
			position=count
		count+=1

	# iterating through specific data and adding the appropriate count to each column 
	for row in df2list(specificdata)[1:]:
		key = row[position]
		value = totaldict[key]
		newrow = row + [value]
		newtable.append(newrow)

	# taking back to df
	newtable = list2df(newtable)

	return newtable


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




