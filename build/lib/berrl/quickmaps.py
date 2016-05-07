from pipehtml import *
from pipegeojson import *
from pipegeohash import *
import pandas as pd
import numpy as np
import itertools
import berrl as bl

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
	elif type=='blocks' or type == 'spark_blocks':
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

# function to create arguments that will be sent into the mapped function
# where splits is the number of constituent dataframes that will 
# created from the og
def make_spark_args(dataframe,splits,**kwargs):
	lines = False
	points = False
	lines_out = False
	for key,value in kwargs.iteritems():
		if key == 'lines':
			lines = value
		elif key == 'points':
			points = value
		elif key == 'lines_out':
			lines_out = value
	# splitting up datafraem into multiple
	frames = np.array_split(dataframe,splits)

	# creating arglist that will be returned 
	arglist = []

	count = 0
	# iterating through each dataframe
	for row in frames:
		count += 1
		filename = 'blocks%s.geojson' % str(count)
		if not points == False:
			filename = 'points%s.geojson' % str(count)
		if lines_out == True:
			filename = 'lines%s.geojson' % str(count)

		if lines == True:
			arglist.append(row)
		elif lines_out == True:
			arglist.append([filename,row])
		else:	
			arglist.append([filename,row])

	return arglist

# function that will be mapped 
# essentially a wrapper for the make_blocks() function
def map_spark_blocks(args):
	# parsing args into filename, and dataframe
	# that will be written to geojson
	filename,dataframe = args[0],args[1]
	#geojson = bl.make_blocks(dataframe,list=True)#,filename=filename
	bl.make_blocks(dataframe,list=True,filename=filename)
	return []

# function that will be mapped 
# essentially a wrapper for the make_points() function
def map_spark_points(args):
	# parsing args into filename, and dataframe
	# that will be written to geojson
	filename,dataframe = args[0],args[1]
	#geojson = bl.make_blocks(dataframe,list=True)#,filename=filename
	bl.make_points(dataframe,list=True,filename=filename)
	return []

# function that will be mapped
def map_spark_lines(args):
	spark_output = True
	filename,table = args
	# taking dataframe to list
	table = bl.df2list(table)

	# getting header
	header = args[0]

	lines = []
	# iterating through each line in the list 
	for row in table[1:]:
		line = bl.make_line([header,row],list=True,postgis=True)
		lines.append(line)
	
	table = lines
	count=0
	total=0
	for row in table:
		count+=1
		# logic to treat rows as outputs of make_line or to perform make_line operation
		if spark_output == False:
			value = make_line([header,row],list=True,postgis=True,alignment_field=alignment_field)
		elif spark_output == True:
			value = row

		# logic for how to handle starting and ending geojson objects
		if row==table[0]:
			#value=make_line([header,row],list=True,postgis=True,alignment_field=alignment_field)
			if not len(table)==2:
				value=value[:-3]
				totalvalue=value+['\t},']
		
		elif row==table[-1]:
			#value=make_line([header,row],list=True,postgis=True,alignment_field=alignment_field)
			value=value[2:]
			totalvalue=totalvalue+value
		else:
			#value=make_line([header,row],list=True,postgis=True,alignment_field=alignment_field)
			value=value[2:-3]
			value=value+['\t},']
			totalvalue=totalvalue+value
	bl.parselist(totalvalue,filename)
	return []

# function that iterates through blocks of lines and writes out appropriately
def map_lines_output(arg):
	spark_output = True

	filename,table = arg

	count=0
	total=0
	for row in table:
		count+=1
		# logic to treat rows as outputs of make_line or to perform make_line operation
		if spark_output == False:
			value = make_line([header,row],list=True,postgis=True,alignment_field=alignment_field)
		elif spark_output == True:
			value = row

		# logic for how to handle starting and ending geojson objects
		if row==table[0]:
			#value=make_line([header,row],list=True,postgis=True,alignment_field=alignment_field)
			if not len(table)==2:
				value=value[:-3]
				totalvalue=value+['\t},']
		
		elif row==table[-1]:
			#value=make_line([header,row],list=True,postgis=True,alignment_field=alignment_field)
			value=value[2:]
			totalvalue=totalvalue+value
		else:
			#value=make_line([header,row],list=True,postgis=True,alignment_field=alignment_field)
			value=value[2:-3]
			value=value+['\t},']
			totalvalue=totalvalue+value
	bl.parselist(totalvalue,filename)
	return []


# parrelize make_blocks 
# attempts to encapsulate a parrelized make_spark_blocks/split
def make_spark_blocks(table,sc):

	args = make_spark_args(table,50)
	concurrent = sc.parallelize(args)
	concurrent.map(map_spark_blocks).collect()
	return []

# parrelize make_blocks 
# attempts to encapsulate a parrelized make_spark_blocks/split
def make_spark_points(table,sc):

	args = make_spark_args(table,50,points=True)
	concurrent = sc.parallelize(args)
	concurrent.map(map_spark_points).collect()
	return []

# makes lines for a postgis database
def make_spark_lines(table,filename,sc,**kwargs):
	spark_output = True
	# removing datetime references from imported postgis database
	# CURRENTLY datetime from postgis dbs throw errors 
	# fields containing dates removed
	list = []
	count = 0
	for row in table.columns.values.tolist():
		if 'date' in row:
			list.append(count)
		count += 1

	table.drop(table.columns[list], axis=1, inplace=True)


	# getting spark arguments
	args = make_spark_args(table,200,lines_output=True)

	# concurrent represents rdd structure that will be parrelized
	concurrent = sc.parallelize(args)

	# getting table that would normally be going into this function
	table = concurrent.map(map_spark_lines).collect()



	'''
	alignment_field = False
	spark_output = True
	if kwargs is not None:
		for key,value in kwargs.iteritems():
			if key == 'alignment_field':
				alignment_field = value 
			if key == 'spark_output':
				spark_output = value

	#changing dataframe to list if dataframe
	if isinstance(table,pd.DataFrame):
		table=df2list(table)
	header=table[0]
	total = []
	# making table the proper iterable for each input 
	if spark_output == True:
		#table = sum(table,[])
		pass
	else:
		table = table[1:]
	'''
	'''
	# making filenames list
	filenames = []
	count = 0
	while not len(filenames) == len(table):
		count += 1
		filename = 'lines%s.geojson' % str(count)
		filenames.append(filename)

	args = []
	# zipping arguments together for each value in table
	for filename,row in itertools.izip(filenames,table):
		args.append([filename,row])


	concurrent = sc.parallelize(args)
	concurrent.map(map_lines_output).collect()
	'''
	'''
	count=0
	total=0
	for row in table:
		count+=1
		# logic to treat rows as outputs of make_line or to perform make_line operation
		if spark_output == False:
			value = make_line([header,row],list=True,postgis=True,alignment_field=alignment_field)
		elif spark_output == True:
			value = row

		# logic for how to handle starting and ending geojson objects
		if row==table[0]:
			#value=make_line([header,row],list=True,postgis=True,alignment_field=alignment_field)
			if not len(table)==2:
				value=value[:-3]
				totalvalue=value+['\t},']
		
		elif row==table[-1]:
			#value=make_line([header,row],list=True,postgis=True,alignment_field=alignment_field)
			value=value[2:]
			totalvalue=totalvalue+value
		else:
			#value=make_line([header,row],list=True,postgis=True,alignment_field=alignment_field)
			value=value[2:-3]
			value=value+['\t},']
			totalvalue=totalvalue+value
		if count == 1000:
			total += count
			count = 0
			print '[%s/%s]' % (total,len(table))
	bl.parselist(totalvalue,filename)
	'''

# makes a certain geojson file based on the type input
def make_type(table,filename,type,**kwargs):
	for key,value in kwargs.iteritems():
		if key == 'sc':
			sc = value
	if type == 'points':
		make_points(table,list=True,filename=filename)
	elif type == 'blocks':
		make_blocks(table,list=True,filename=filename)
	elif type == 'line':
		make_line(table,list=True,filename=filename)
	elif type == 'polygon':
		make_polygon(table,list=True,filename=filename)
	elif type == 'lines':
		make_postgis_lines(table,filename)
	elif type == 'polygons':
		make_postgis_polygons(table,filename)
	elif type == 'spark_blocks':
		make_spark_blocks(table,sc)
	elif type == 'spark_points':
		make_spark_points(table,sc)
	elif type == 'spark_lines':
		make_spark_lines(table,filename,sc)

# function that returns a list of 51 gradient blue to red heatmap 
def get_heatmap51():
	list = ['#0030E5', '#0042E4', '#0053E4', '#0064E4', '#0075E4', '#0186E4', '#0198E3', '#01A8E3', '#01B9E3', '#01CAE3', '#02DBE3', '#02E2D9', '#02E2C8', '#02E2B7', '#02E2A6', '#03E295', '#03E184', '#03E174', '#03E163', '#03E152', '#04E142', '#04E031', '#04E021', '#04E010', '#09E004', '#19E005', '#2ADF05', '#3BDF05', '#4BDF05', '#5BDF05', '#6CDF06', '#7CDE06', '#8CDE06', '#9DDE06', '#ADDE06', '#BDDE07', '#CDDD07', '#DDDD07', '#DDCD07', '#DDBD07', '#DCAD08', '#DC9D08', '#DC8D08', '#DC7D08', '#DC6D08', '#DB5D09', '#DB4D09', '#DB3D09', '#DB2E09', '#DB1E09', '#DB0F0A']
	return list

# checks to see if all the float values in a gradient range are equal to the integer value 
def check_gradient_ints(rangelist):
	ind = 0
	for row in rangelist:
		if not int(row) == float(row):
			ind = 1
	if ind == 0:
		newrangelist = []
		for row in rangelist:
			newrangelist.append(int(row))
	else:
		newrangelist = rangelist

	return newrangelist


# given a minimum value maximum value returns a list of ranges
# this list of ranges can be sent into make_object_map()
def make_gradient_range(min,max,heatmaplist):
	# getting the step size delta for making the heatmap list
	delta = (float(max) - float(min)) / len(heatmaplist)
	
	# setting the current step size to the minimum
	current = min

	# instantiating rangelist
	rangelist = []

	# iterating through the 
	while not len(rangelist) == len(heatmaplist):
		rangelist.append(current)
		current += delta

	# checking range values to see if floats can be reduced to ints
	rangelist = check_gradient_ints(rangelist)

	return rangelist

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
				filename = color.replace('#','') + '2.geojson'
			else:
				filename = color.replace('#','') + '.geojson'
			try:
				if not len(temp)==0:
					make_type(temp,filename,type)
					colordict[filename] = color
				else:
					make_type(dummy,filename,type)
					colordict[filename] = color
			except Exception:
				make_type(dummy,filename.replace('#',''),type)
				colordict[filename] = color
			oldrow=row
	return colordict



