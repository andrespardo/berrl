from pipehtml import *
from pipegeojson import *
from pipegeohash import *
import pandas as pd
import numpy as np
import itertools

def map_axis_unique(dataframe,uniqueaxis,**kwargs):
	return_filenames=False
	return_spark=False
	for key,value in kwargs.iteritems():
		if key=='return_filenames':
			if value==True:
				return_filenames=True
	uniques=np.unique(dataframe[str(uniqueaxis)]).tolist()
	colors=['light green','blue','red','yellow','light blue','orange','purple','green','brown','pink','default']

	filenames=[]
	for a,b in itertools.izip(uniques,colors):
		temp=dataframe[dataframe[uniqueaxis]==a]
		temp['color']=b
		templines=make_points(temp,list=True)
		filename=b+'.geojson'
		parselist(templines,filename)
		filenames.append(filename)
	if not return_filenames==True:
		loadparsehtml(filenames,colorkey='color')
	else:
		return filenames


def heatmap(data,precision,**kwargs):
	return_filenames=False
	return_spark=False
	return_both=False
	for key,value in kwargs.iteritems():
		if key=='return_filenames':
			if value==True:
				return_filenames=True
		elif key=='return_spark':
			if value==True:
				return_spark=True
		elif key=='return_both':
			if value==True:
				return_both=True
	#mapping table and reading data
	map_table(data,precision,list=True)
	data=pd.read_csv('squares'+str(precision)+'.csv')

	# creating factor
	#setting up heat map
	maxvalue=data['COUNT'].max()
	factor=maxvalue/5

	# one may have to adjust to get a desired distribution of different colors
	# i generally like my distributions a little more logarithmic
	# a more definitive algorithm for sliding factors to achieve the correct distributions will be made later
	factors=[0,factor*.5,factor*1,factor*2,factor*3,factor*6]
	colors=['','blue','light blue','light green','yellow','red']

	# making geojson files
	filenames=[]
	sparks=[]
	count=0
	for a,b in itertools.izip(factors,colors):
		if count==0:
			count=1
			oldrow=a
		else:
			temp=data[(data.COUNT>=oldrow)&(data.COUNT<a)]
			count+=1
			oldrow=a
			temp['color']=b
			if len(temp)==0:
				temp=[temp.columns.values.tolist()]
				add=[]
				count2=0
				while not count2==len(temp[0]):
					count2+=1
					add.append(0)
				temp=temp+[add]
				temp=list2df(temp)
			filenames.append(str(b)+'.geojson')
			sparks.append([temp,'blocks',str(b)+'.geojson'])
	if return_filenames==True:
		return filenames
	if return_spark==True:
		return sparks
	if return_both==True:
		return [filenames,sparks]

# given a list of postgis lines returns a list of dummy lines as a place holder for a file style
def make_dummy_lines(header):
	newlist=[header]
	linestring='SRID=4326;MULTILINESTRINGM((0 0 0,0 0 0,0 0 0))'
	count=0
	ind=0
	while not count==5:	
		values=[]
		count+=1
		for row in header:
			if row=='st_asewkt':
				values.append(linestring)
			elif ind==0:
				ind=1
				values.append(count)
			else:
				values.append('null')
		ind=0
		newlist.append(values)

	return list2df(newlist)

# makes dummy polygons for a given postgis list of polygons
def make_dummy_polygons(header):
	newlist=[header]
	linestring='SRID=4326;MULTILINESTRINGM((0 0,0 0,0 0))'
	count=0
	ind=0
	while not count==5:	
		values=[]
		count+=1
		for row in header:
			if row=='st_asewkt':
				values.append(linestring)
			elif ind==0:
				ind=1
				values.append(count)
			else:
				values.append('null')
		ind=0
		newlist.append(values)

	return list2df(newlist)

# makes a dummy value for points
def make_dummy_points(header):
	newlist=[header]
	ind=0
	count=0
	while not count==5:	
		values=[]
		count+=1
		for row in header:
			if 'lat' in str(row).lower() or 'long' in str(row).lower():
				values.append(0)
			elif ind==0:
				ind=1
				values.append(count)
			else:
				values.append('null')
		ind=0
		newlist.append(values)
	return list2df(newlist)

# makes a dummy value for blocks
def make_dummy_blocks(header):
	newlist=[header]
	ind=0
	count=0
	while not count==5:	
		values=[]
		count+=1
		for row in header:
			if 'lat' in str(row).lower() or 'long' in str(row).lower():
				values.append(0)
			elif ind==0:
				ind=1
				values.append(count)
			else:
				values.append('null')
		ind=0
		newlist.append(values)
	return list2df(newlist)

# makes a dummy value given a header and type
def make_dummy(header,type):
	if type=='lines':
		dummy=make_dummy_lines(header)
	elif type=='polygons':
		dummy=make_dummy_polygons(header)
	elif type=='points':
		dummy=make_dummy_points(header)
	elif type=='blocks':
		dummy=make_dummy_blocks(header)
	return dummy


# generator
def yieldgen(list):
	for row in list:
		yield row


#takes a dataframe and turns it into a list
def df2list(df):
    df = [df.columns.values.tolist()]+df.values.tolist()
    return df

#takes a list and turns it into a datafrae
def list2df(df):
    df = pd.DataFrame(df[1:], columns=df[0])
    return df

# given a table a column header and a range returns list inbetween ranges writes out to filename given
def get_range(table,headercolumn,min,max):
	# maximum value will always be equal to 
	temp = table[(table[headercolumn] > min) & (table[headercolumn] <= max)]
	return temp

# makes a certain geojson file based on the type input
def make_type(table,filename,type):
	if type == 'points':
		make_points(table,list=True,filename=filename)
	elif type == 'blocks':
		make_blocks(table,list=True,filename=filename)
	elif type == 'lines':
		make_postgis_lines(table,filename)
	elif type == 'polygons':
		make_postgis_polygons(table,filename)


# makes sliding heat table 
def make_object_map(table,headercolumn,ranges,colors,type,**kwargs):
	# table is a dataframe object
	# ranges is a list of ranges to go in between
	# headercolumn is the colomn in which to pivot the ranges
	# colors is the color for each range delta should be len(ranges)-1 size
	# type is the type of object it is
	filenames=False
	for key,value in kwargs.iteritems():
		if 'filenames'==key:
			filenames=value

	count = 0
	dummy = make_dummy(table.columns.values.tolist(),type)
	for row in ranges:
		if count == 0:
			count = 1 
			oldrow = row
			colorgenerator = yieldgen(colors)
			colordict = {}
		else:
			temp = get_range(table,headercolumn,oldrow,row)
			color = next(colorgenerator)
			if filenames==True:
				filename = color + '2.geojson'
			else:
				filename = color + '.geojson'
			try:
				if not len(temp)==0:
					make_type(temp,filename,type)
					colordict[filename] = color
				else:
					make_type(dummy,filename,type)
					colordict[filename] = color
			except Exception:
				make_type(dummy,filename,type)
				colordict[filename] = color
			oldrow=row
	return colordict




