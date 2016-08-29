from pipehtml import *
from pipegeojson import *
from pipegeohash import *
import pandas as pd
import numpy as np
import itertools
import warnings
warnings.simplefilter(action = "ignore", category = Warning)

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

# given a dataframe and a list of columnsn 
# drops columns from df
def drop_columns(table,columns):
	list = []
	count = 0
	for row in columns:
		columnrow = row
		for row in table.columns.values.tolist():
			if columnrow in row:
				list.append(count)
			count += 1

	table.drop(table.columns[list], axis=1, inplace=True)	
	return table

# for a given column header and a given unique value 
# returns a new df of the same size with a new column 
# of the unique with 1 or 0 being whether or not it contains
# the unique int the field
def add_column(data,headercolumn,unique):
	data['BOOL'] = data[headercolumn].isin([unique])

	# getting true values first
	truedf = data[data.BOOL == True]
	truedf[unique] = 1
	truedf = drop_columns(truedf,['BOOL'])
	falsedf = data[data.BOOL == False]
	falsedf[unique] = 0
	falsedf = drop_columns(falsedf,['BOOL'])

	data = pd.concat([truedf,falsedf])
	return data

def add_columns(data,headercolumn,uniques):
	for row in uniques:
		unique = row
		data = add_column(data,headercolumn,unique)
	return uniques,data

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
	if min == 0:
		temp = table[(table[headercolumn] >= min) & (table[headercolumn] <= max)]
	else:
		temp = table[(table[headercolumn] > min) & (table[headercolumn] <= max)]
	return temp

# function to create arguments that will be sent into the mapped function
# where splits is the number of constituent dataframes that will 
# created from the og
def make_spark_args(dataframe,splits,**kwargs):
	lines = False
	points = False
	lines_out = False
	lines_out_count = False
	blocks = False
	extrema = False
	for key,value in kwargs.iteritems():
		if key == 'lines':
			lines = value
		elif key == 'points':
			points = value
		elif key == 'lines_out':
			lines_out = value
		elif key == 'lines_out_count':
			lines_out_count = value
		elif key == 'blocks':
			blocks = value
		elif key == 'extrema':
			extrema = value
	# splitting up datafraem into multiple
	frames = np.array_split(dataframe,splits)

	if blocks == True:
		args = make_spark_args_blocks(dataframe,splits)
		return args

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
		if not lines_out_count == False:
			filename = 'lines%s_%s.geojson' % (str(count),str(lines_out_count))
		if lines == True:
			arglist.append(row)
		elif lines_out == True and not extrema == False:
			arglist.append([filename,row,extrema])
		elif lines_out == True:
			arglist.append([filename,row])
		else:	
			arglist.append([filename,row])

	return arglist


# given a slice of a split blocksframe 
# returns a list of y value ranges to slice each horizontal frame by
def make_blocks_range(frame,dimsize):
	miny,maxy = frame['Y'].min(),frame['Y'].max()

	delta = (maxy - miny) / dimsize

	rangelist = []
	current = miny
	while current < len(frame) and not len(rangelist) == dimsize - 1:
		newcurrent = current + delta
		rangelist.append([current,newcurrent])
		current = newcurrent

	rangelist.append([current,( maxy + 1)])

	return rangelist

# making spark args for new blocks syntax format and slicing
def make_spark_args_blocks(table,dimsize):
	# creating vertical columns of the dimsize already split horizontally
	frames = np.array_split(table,dimsize)
	# creates a list of 2d lists containing slice ranges of the y axis
	# a few assumptions made for like a partial horizntal row will be neglible
	yranges = make_blocks_range(frames[0],dimsize)
	count = 0
	arglist = []
	extremadict = {}
	for row in frames:
		temp = row
		for row in yranges:
			count += 1
			min,max = row
			newtemp = temp[(temp['Y'] >= min) & (temp['Y'] < max)]
			
			# getting extrema of newtemp
			minlat,maxlat = newtemp['LAT1'].min(),newtemp['LAT4'].max()
			minlong,maxlong = newtemp['LONG1'].min(),newtemp['LONG4'].max()
			extrema = {'n':maxlat,'s':minlat,'w':minlong,'e':maxlong}
			avglat = (extrema['n'] + extrema['s']) / 2.0
			avglong = (extrema['e'] + extrema['w']) / 2.0

			# getting filename
			filename = 'blocks%s.geojson' % (str(count))

			# adding to dictionary entry
			extremadict[filename] = [avglong,avglat]

			arglist.append([filename,newtemp])
	
	with open('blocks_info.json','wb') as newjson:
		json.dump(extremadict,newjson)

	return arglist



# function that will be mapped 
# essentially a wrapper for the make_blocks() function
def map_spark_blocks(args):
	# parsing args into filename, and dataframe
	# that will be written to geojson
	filename,dataframe = args[0],args[1]
	#geojson = bl.make_blocks(dataframe,list=True)#,filename=filename
	make_blocks(dataframe,list=True,filename=filename,bounds=True)
	return []

# function that will be mapped 
# essentially a wrapper for the make_points() function
def map_spark_points(args):
	# parsing args into filename, and dataframe
	# that will be written to geojson
	filename,dataframe = args[0],args[1]
	#geojson = bl.make_blocks(dataframe,list=True)#,filename=filename
	make_points(dataframe,list=True,filename=filename)
	return []

# function that will be mapped
def map_spark_lines(args):
	extrema = False
	spark_output = True
	lines = False
	if len(args) == 3:
		filename,table,extrema = args
	else:
		filename,table = args
	# taking dataframe to list
	table = df2list(table)

	# getting header
	header = table[0]

	count = 0
	# iterating through each line in the list 
	for row in table[1:]:
		line = make_line([header,row],list=True,postgis=True,bounds=True,extrema=extrema)
		if not line == False:
			if count == 0:
				count = 1
				lines = line
			else:
				lines['features'].append(line['features'][0])
			

	count=0
	total=0

	#bl.parselist(totalvalue,filename)
	if not lines == False:
		with open(filename,'wb') as newgeojson:
			json.dump(lines,newgeojson)
			print 'Wrote %s to geojson.' % filename
	return []

# parrelize make_blocks 
# attempts to encapsulate a parrelized make_spark_blocks/split
def make_spark_blocks(table,sc):
	blocks = False
	splits = False

	args = make_spark_args(table,4,blocks=True)
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
	lines_out_count = False
	extrema = False
	for key,value in kwargs.iteritems():
		if key == 'lines_out_count':
			lines_out_count = value
		if key == 'extrema':
			extrema = value
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
	if lines_out_count == False:
		args = make_spark_args(table,25,lines_out = True,extrema=extrema)
	else:
		args = make_spark_args(table,25,lines_out_count=lines_out_count)
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


def make_spark_filenames(type,setcount):
	count = 0
	filenames = []
	if type == 'lines':
		while not count == 50:
			count += 1
			filename = 'lines%s_%s.geojson' % (str(count),str(setcount))
			filenames.append(filename)
		return filenames


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

def get_heatmap10():
	list = ['#0075E4', '#01CAE3', '#02E2A6', '#03E152', '#09E004', '#5BDF05', '#ADDE06', '#DDBD07', '#DC6D08', '#DB1E09'] 
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

# for a list of columns gets the maximum values within a dataframe range
def get_maxes(columns,data):
	maxlist = []
	for row in columns:
		newmax = data[row].max()
		maxlist.append(newmax)
	return maxlist

# given a dataframe and a list of maximum values for a zoom range 
# and a dict returns a returns an udated dict with geohash point height stores
def get_heights(squares,maxlistzoom,heightsdict):
	headers = squares.columns.values.tolist()
	newheaderlist = []
	for headerval,maxval in itertools.izip(headers[1:],maxlistzoom[1:]):
		squares[headerval+'1'] = (squares[headerval].astype(float)/float(maxval)) * 300
		squares[headerval+'1'] = squares[headerval+'1'].astype(int)
		newheaderlist.append(headerval+'1')
	
	squareheights = squares[newheaderlist]
	
	return squareheights

# makes zoom blocks for given levels and zoom ranges
def make_zoom_blocks(table,levels,zooms,**kwargs):
	field = 'COUNT'
	columns = []
	create_columns = []
	heatmap_size = 51
	distributed = False
	all_fields = False
	for key,value in kwargs.iteritems():
		if 'field' == key:
			field = value
		if 'columns' == key:
			columns = value
		if 'heatmap_size' == key:
			heatmap_size = value
		if 'distributed' == key:
			distributed = value
		if 'all_fields' == key:
			all_fields = value

	# getting squares
	squares = map_table(table,8,columns=columns,return_squares=True)
	
	# getting header 
	header = squares.columns.values.tolist()

	# getting the list of squares
	squares = make_geohash_tables(squares,levels,return_squares=True,sort_by=field)

	count = 0
	combinedfiledict = {}
	heightdict = {}
	zoom_dict = {}
	squaresmult = squares
	for precision,zoomlist,squares in itertools.izip(levels,zooms,reversed(squaresmult)):
		count += 1
		# getting maxs for the given zoom level
		#maxlistzoom = get_maxes(columns,squares[columns])
		#squareheights = get_heights(squares[['GEOHASH']+columns],['GEOHASH']+maxlistzoom,heightdict)	
		
		# adding squareheights to squares list
		#squares[squareheights.columns.values.tolist()] = squareheights
		
		# logic for deteermining what heatmap to use
		if heatmap_size == 51:
			colors = get_heatmap51()
		elif heatmap_size == 10:
			colors = get_heatmap10()
		
		squaresmin,squaresmax = squares[field].min(),squares[field].max()
		#colorrange = make_gradient_range(squaresmin,squaresmax,colors)
		if distributed == True:
			colors,colorrange = make_distributed_range(squares,field)
		else:
			colors,colorrange = make_gradient_range(squaresmin,squaresmax,colors)
		# filedict returned from this iteration of make objects
		
		squares = make_object_map_colorkey(squares,field,colorrange,colors)
		if all_fields == True:
			for row in columns:
				newfield = row
				squaresmin,squaresmax = squares[newfield].min(),squares[newfield].max()
				if distributed == True and not heatmap_size > squaresmax:
					colors,colorrange = make_distributed_range(squares,newfield)
				else:
					colors,colorrange = make_gradient_range(squaresmin,squaresmax,colors)
				squares = make_object_map_colorkey(squares,newfield,colorrange,colors)			
		make_blocks(squares,list=True,filename='squares' + str(count) + '.geojson')

		#combinedfiledict = dict(combinedfiledict.items() + filedict.items())

		# getting filenames from the output of make_object_map

		# getting zoom dict from the filenames 
		zoom_dict['squares' + str(count) + '.geojson'] = zoomlist

	headers = squares.columns.values.tolist()
	newheaders = []
	for row in headers:
		if not 'LAT' in str(row).upper() and not 'LONG' in str(row).upper():
			newheaders.append(row)
	headers = newheaders

	if all_fields == True:
		position = len(columns) + 1
		colorkeyfields = headers[-position:]
		zoom_dict['headers'] = headers
		return zoom_dict,colorkeyfields
	else:
		colorkeyfield = headers[-1]
		zoom_dict['headers'] = headers
		return zoom_dict,colorkeyfield


# given a minimum value maximum value returns a list of ranges
# this list of ranges can be sent into make_object_map()
def make_gradient_range(min,max,heatmaplist):
	# if the size of the gradient color range given is larger then the
	# size of the maximum value 
	# restructures colorlist for values given
	if len(heatmaplist) > max:
		factor = round(len(heatmaplist))/round(max)
		current = 0
		newheatmaplist = []
		while current < len(heatmaplist) and not max == len(newheatmaplist):
			current += factor
			position = round(current,0) - 1
			if len(heatmaplist) < current:
				print current,len(newheatmaplist),max
			newheatmaplist.append(heatmaplist[int(position)])
		newheatmaplist = newheatmaplist[:-1] + [heatmaplist[-1]] 
		heatmaplist = newheatmaplist

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

	return heatmaplist,rangelist

# given a maximum value checks to see if value is int or float based on maximum value
def get_max_col(maxval):
	if int(maxval) == float(maxval):
		return True
	else:
		return False


# given a rangelist makes a histogram table 
def make_histo(table,rangelist,field,intbool):
	newlist = [['RANGE',field]]
	count = 0
	for row in rangelist:
		if count == 0:
			count = 1
		else:
			if intbool == True:
				row = int(row)
				oldrow = int(oldrow)
			temp = get_range(table,field,oldrow,row)
			rangestring = str(oldrow) + '-' + str(row)
			tempcount = len(temp)
			newrow = [rangestring,tempcount]
			newlist.append(newrow)
		oldrow = row
	newlist = list2df(newlist)
	return newlist


# gets the zero portion of a list 
# this returned df will have its ranges stretched to flatten out the ranges
# reducing the size of this df 
def get_zero_portion(histo):
	count = 0
	ind = 0
	indexfirstzero = 0
	for row in df2list(histo)[1:]:
		if row[1] == 0 and ind == 0:
			indexfirstzero = count - 1
			ind = 1
		count +=1
	if indexfirstzero == 0:
		return []
	zeroportion = histo[indexfirstzero:]
	return zeroportion


# gets the zero portion of a list 
# this returned df will have its ranges stretched to flatten out the ranges
# reducing the size of this df 
def get_nonzero_portion(histo):
	count = 0
	ind = 0
	for row in df2list(histo)[1:]:
		if row[1] == 0 and ind == 0:
			indexfirstzero = count - 1
			ind = 1
		count +=1

	zeroportion = histo[:indexfirstzero - 1]
	return zeroportion


# gets the rangelist for zero portion that is flattened
def get_rangelist_zeroportion(zeroportion):
	newranges = []
	count = 0
	for row in df2list(zeroportion)[1:]:
		if row[1] > 0:
			lastrange = int(str.split(row[0],'-')[0])
			if count == 0:
				count = 1
			else:
				newranges.append(oldlastrange)
			oldlastrange = lastrange
	newranges.append(lastrange)

	return newranges


# gets the first value in nonzeroportion list
def get_first_nonzero(nonzeroportion,headerval,intbool):
	# sorting by maximum range count
	headerval = nonzeroportion.columns.values.tolist()[1]
	nonzeroportion = nonzeroportion.sort([headerval],ascending = [0])

	# getting maximum range count row
	firstrow = df2list(nonzeroportion)[1]

	# getting the first rows first range value
	if intbool == True:
		firstrangevalue = int(str.split(firstrow[0],'-')[0])
	else:
		firstrangevalue = float(str.split(firstrow[0],'-')[0])


	return firstrangevalue


# reduce color list by the ending size of totallist 
def reduce_color_list_size(totallist,colorlist):
	delta = float(len(colorlist)) / float(len(totallist))
	current = 0
	newrangelistpositions = []

	# getting all the range positions for the new list
	while current < len(colorlist) and not len(newrangelistpositions) ==  len(totallist):
		newrangelistpositions.append(int(current))
		current += delta

	newrangelistpositions = newrangelistpositions[:-1] + [len(colorlist) - 1]

	# iterating through each position index and compiling new colorlist
	newcolorlist = []
	for row in newrangelistpositions:
		newcolor = colorlist[row]
		newcolorlist.append(newcolor)

	return newcolorlist

# from a dataset and a field makes a colorlist and range list for the field given
def make_distributed_range(data,field):
	# getting maximum and minium values in each field
	maxval = data[field].max()
	minval = data[field].min()


	# checks to see if field is int 
	# currently works for only ints
	intbool = get_max_col(maxval)

	# a starting colormap list that will be reduced as needed
	heatmap51 = get_heatmap51()

	if maxval < len(heatmap51):
		return make_gradient_range(minval,maxval,heatmap51)

	# making a rangelist for a baseline histo
	blank,rangelist = make_gradient_range(minval,maxval,heatmap51)

	# makes a histogram then seperates the ranges into two different sections
	newlist = make_histo(data,rangelist,field,intbool)
	zeroportion = get_zero_portion(newlist)
	if len(zeroportion) == 0:
		return make_gradient_range(minval,maxval,heatmap51)
	nonzeroportion = get_nonzero_portion(newlist)

	# getting zero portion of range list
	zero_portion_rangelist = get_rangelist_zeroportion(zeroportion)

	# assembles variables needed for nonzero portion range list creation
	firstval = get_first_nonzero(nonzeroportion,field,intbool)
	nonzeroportionsize = nonzeroportion[field].sum()
	remainingsize = len(heatmap51) - len(nonzeroportion)
	delta = nonzeroportionsize / remainingsize

	# creates the nonzero portion of the list
	lastrange = 0
	firstrange = firstval - 1
	partitionlistnonzero = [0]
	partitionsize = 0
	while not len(partitionlistnonzero) == remainingsize and zero_portion_rangelist[0] > firstrange:
		while partitionsize < delta and zero_portion_rangelist[0] > firstrange:
			firstrange += 1
			temp = get_range(data,field,lastrange,firstrange)
			partitionsize = len(temp)
		partitionlistnonzero.append(firstrange)
		partitionsize = 0
		lastrange = firstrange

	# assembling the totallist from each portion
	totallist = partitionlistnonzero[:-1] + zero_portion_rangelist
	if totallist[1]  == totallist[2]:
		return make_gradient_range(minval,maxval,heatmap51)
	
	# appending the last and maximum value
	totallist.append(maxval)
	
	#print make_histo(data,totallist,field,intbool)
	# assembling the new color list from the size of the totallist
	newcolorlist = reduce_color_list_size(totallist,heatmap51)
	return newcolorlist,totallist


# makes sliding heat table 
def make_object_map_dep(table,headercolumn,ranges,colors,type,**kwargs):
	# table is a dataframe object
	# ranges is a list of ranges to go in between
	# headercolumn is the colomn in which to pivot the ranges
	# colors is the color for each range delta should be len(ranges)-1 size
	# type is the type of object it is
	filenames_count = False
	for key,value in kwargs.iteritems():
		if 'filenames_count' == key:
			filenames_count = value

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
			if not filenames_count == False:
				filename = color.replace('#','') + '_' + str(filenames_count) +'.geojson'
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


# makes sliding heat table 
def make_object_map_colorkey(table,headercolumn,ranges,colors,**kwargs):
	# table is a dataframe object
	# ranges is a list of ranges to go in between
	# headercolumn is the colomn in which to pivot the ranges
	# colors is the color for each range delta should be len(ranges)-1 size
	# type is the type of object it is
	filenames_count = False
	for key,value in kwargs.iteritems():
		if 'filenames_count' == key:
			filenames_count = value

	count = 0
	listofdfs = []
	for row in ranges:
		if count == 0:
			count = 1 
			oldrow = row
			colorgenerator = yieldgen(colors)
			colordict = {}
		else:
			temp = get_range(table,headercolumn,oldrow,row)
			color = next(colorgenerator)
			try:
				if not len(temp)==0:
					temp['COLORKEY' + '_' +str(headercolumn)] = color
					listofdfs.append(temp)
				else:
					pass
			except Exception:
				print 'passed',oldrow,row,headercolumn,'error'
				pass
			oldrow=row
	newdf = pd.concat(listofdfs)
	return newdf



# make file zoom dictionary for a given range
def make_zoom_dict(filenames,extremazoomlist,inputdictionary):
	# setting the new dictionary to the input dictionary to append values
	# from input into the newdictionary
	newdictionary = inputdictionary
	
	# iterating through each filename
	for row in filenames:
		newdictionary[str(row)] = extremazoomlist

	return newdictionary

# function for getting all non zooms and colorfield keys
def get_keys(file_dictionary,filename):
	newkeys = []
	for row in file_dictionary[str(filename)].keys():
		if not str(row) == 'zooms' and not str(row) == 'colorkeyfields' and not 'slider_' in str(row):
			newkeys.append(str(row))
	return newkeys

def get_sliders(file_dictionary,filename):
	newkeys = []
	for row in file_dictionary[str(filename)].keys():
		if 'slider_' in str(row):
			newkeys.append(str(row))
	return newkeys

# function for expanding out like fields in a file_dictionary
# this function will be modified once filters are removed when reaching a new zoom level
def expand_out(file_dictionary):
	# getting the non slider key list
	keylist = []
	for row in file_dictionary.keys():
		keys = get_keys(file_dictionary,str(row))
		keylist.append([row,keys])
	
	# creating a field, file dictionary containing each field
	uniques = []
	uniquedict = {}
	for row in keylist:
		oldoldrow = row
		newrow = row[1]
		for row in newrow:
			oldrow = row
			ind = 0
			for row in uniques:
				if oldrow == row:
					ind = 1
			if not ind == 1:
				uniques.append(oldrow)
				uniquedict[str(oldrow)] = [oldoldrow[0]]
			else:
				uniquedict[str(oldrow)].append(oldoldrow[0])
	
	# getting only the values with more than 1 value in the list
	newuniquedict = {}
	for row in uniquedict.keys():
		if len(uniquedict[row]) > 1:
			newuniquedict[row] = uniquedict[row]

	# compiling unique values getting the uniques of those and modifying 
	# the file dictionary
	for row in newuniquedict.keys():
		shared = str(row)
		total = []
		for row in newuniquedict[shared]:
			total += file_dictionary[row][shared]
		combineduniques = np.unique(total).tolist()
		for row in newuniquedict[shared]:
			file_dictionary[row][shared] = combineduniques

	# getting the slider key list
	keylist = []
	for row in file_dictionary.keys():
		keys = get_sliders(file_dictionary,str(row))
		keylist.append([row,keys])

	# creating a field, file dictionary containing each slider field
	uniques = []
	uniquedict = {}
	for row in keylist:
		oldoldrow = row
		newrow = row[1]
		for row in newrow:
			oldrow = row
			ind = 0
			for row in uniques:
				if oldrow == row:
					ind = 1
			if not ind == 1:
				uniques.append(oldrow)
				uniquedict[str(oldrow)] = [oldoldrow[0]]
			else:
				uniquedict[str(oldrow)].append(oldoldrow[0])
	
	# getting only the values with more than 1 value in the list
	newuniquedict = {}
	for row in uniquedict.keys():
		if len(uniquedict[row]) > 1:
			newuniquedict[row] = uniquedict[row]

	for row in newuniquedict.keys():
		shared = str(row)
		mins = []
		maxs = []
		for row in newuniquedict[str(shared)]:
			mintemp,maxtemp = file_dictionary[row][shared][0],file_dictionary[row][shared][1]
			mins.append(mintemp)
			maxs.append(maxtemp)
		mintotal,maxtotal = min(mins),max(maxs)
		extrema = [mintotal,maxtotal]
		for row in newuniquedict[str(shared)]:
			print extrema,file_dictionary[row][shared]			
			file_dictionary[row][shared] = extrema


	return file_dictionary

###############################################################################################################################																				

# currently support only int sliders
def make_file_dict(filename,table,fields,**kwargs):
	file_dictionary = {}
	slider_fields = False
	colorkeyfields = False
	zooms = False
	expand = False
	chart_dictionary = False
	for key,value in kwargs.iteritems():
		if key == 'file_dictionary':
			file_dictionary = value
		if key == 'slider_fields':
			slider_fields = value
		if key == 'colorkeyfields':
			colorkeyfields = value
		if key == 'zooms':
			zooms = value
		if key == 'expand':
			expand = value
		if key == 'chart_dictionary':
			chart_dictionary = value
	tempdict = {}
	for row in fields:
		field = str(row)
		temp = np.unique(table[str(row)]).tolist()
		newtemp = []
		for row in temp:
			if row == True:
				row = str('true')
			elif row == False:
				row = str('false')
			newtemp.append(row)
		temp = newtemp
		tempdict[str(field)] = temp
	if not slider_fields == False:
		for row in slider_fields:
			bounds = [table[str(row)].min(),table[str(row)].max()]
			tempdict['slider_' + str(row)] = bounds

	# logic for adding zooms and colorkeyfields if kwarg is input
	if not colorkeyfields == False:
		tempdict['colorkeyfields'] = colorkeyfields
	# logic for zooms
	if not zooms == False:
		tempdict['zooms'] = zooms
	# adding a zchart_dictionary if applicable
	if not chart_dictionary == False:
		tempdict['chart_dictionary'] = chart_dictionary

	file_dictionary[str(filename)] = tempdict
	if expand == True:
		file_dictionary = expand_out(file_dictionary)

	return file_dictionary

# generates a large heatmap of around 1000 colorkeys
def get_heatmaplarge():
	return ['#113ef2', '#113ff2', '#1140f2', '#1141f2', '#1142f2', '#1143f2', '#1144f2', '#1145f2', '#1146f2', '#1147f2', '#1148f2', '#1149f2', '#114af2', '#114bf2', '#114cf2', '#114df2', '#124cf3', '#124df3', '#124ef3', '#124ff3', '#1250f3', '#1251f3', '#1252f3', '#1253f3', '#1254f3', '#1255f3', '#1256f3', '#1257f3', '#1258f3', '#1259f3', '#125af3', '#125bf3', '#125af3', '#125bf3', '#125cf3', '#125df3', '#125ef3', '#125ff3', '#1260f3', '#1261f3', '#1262f3', '#1263f3', '#1264f3', '#1265f3', '#1266f3', '#1267f3', '#1268f3', '#1269f3', '#1268f3', '#1269f3', '#126af3', '#126bf3', '#126cf3', '#126df3', '#126ef3', '#126ff3', '#1270f3', '#1271f3', '#1272f3', '#1273f3', '#1274f3', '#1275f3', '#1276f3', '#1277f3', '#1276f3', '#1277f3', '#1278f3', '#1279f3', '#127af3', '#127bf3', '#127cf3', '#127df3', '#127ef3', '#127ff3', '#1280f3', '#1281f3', '#1282f3', '#1283f3', '#1284f3', '#1285f3', '#1284f3', '#1285f3', '#1286f3', '#1287f3', '#1288f3', '#1289f3', '#128af3', '#128bf3', '#128cf3', '#128df3', '#128ef3', '#128ff3', '#1290f3', '#1291f3', '#1292f3', '#1293f3', '#1292f3', '#1293f3', '#1294f3', '#1295f3', '#1296f3', '#1297f3', '#1298f3', '#1299f3', '#129af3', '#129bf3', '#129cf3', '#129df3', '#129ef3', '#129ff3', '#12a0f3', '#12a1f3', '#12a0f4', '#12a1f4', '#12a2f4', '#12a3f4', '#12a4f4', '#12a5f4', '#12a6f4', '#12a7f4', '#12a8f4', '#12a9f4', '#12aaf4', '#12abf4', '#12acf4', '#12adf4', '#12aef4', '#12aff4', '#12aef4', '#12aff4', '#12b0f4', '#12b1f4', '#12b2f4', '#12b3f4', '#12b4f4', '#12b5f4', '#12b6f4', '#12b7f4', '#12b8f4', '#12b9f4', '#12baf4', '#12bbf4', '#12bcf4', '#12bdf4', '#12bcf4', '#12bdf4', '#12bef4', '#12bff4', '#12c0f4', '#12c1f4', '#12c2f4', '#12c3f4', '#12c4f4', '#12c5f4', '#12c6f4', '#12c7f4', '#12c8f4', '#12c9f4', '#12caf4', '#12cbf4', '#12caf4', '#12cbf4', '#12ccf4', '#12cdf4', '#12cef4', '#12cff4', '#12d0f4', '#12d1f4', '#12d2f4', '#12d3f4', '#12d4f4', '#12d5f4', '#12d6f4', '#12d7f4', '#12d8f4', '#12d9f4', '#12d9f4', '#12daf4', '#12dbf4', '#12dcf4', '#12ddf4', '#12def4', '#12dff4', '#12e0f4', '#12e1f4', '#12e2f4', '#12e3f4', '#12e4f4', '#12e5f4', '#12e6f4', '#12e7f4', '#12e8f4', '#12e7f4', '#12e8f4', '#12e9f4', '#12eaf4', '#12ebf4', '#12ecf4', '#12edf4', '#12eef4', '#12eff4', '#12f0f4', '#12f1f4', '#12f2f4', '#12f3f4', '#12f4f4', '#12f5f4', '#12f6f4', '#12f5f4', '#12f5f3', '#12f5f2', '#12f5f1', '#12f5f0', '#12f5ef', '#12f5ee', '#12f5ed', '#12f5ec', '#12f5eb', '#12f5ea', '#12f5e9', '#12f5e8', '#12f5e7', '#12f5e6', '#12f5e5', '#12f5e6', '#12f5e5', '#12f5e4', '#12f5e3', '#12f5e2', '#12f5e1', '#12f5e0', '#12f5df', '#12f5de', '#12f5dd', '#12f5dc', '#12f5db', '#12f5da', '#12f5d9', '#12f5d8', '#12f5d7', '#12f5d8', '#12f5d7', '#12f5d6', '#12f5d5', '#12f5d4', '#12f5d3', '#12f5d2', '#12f5d1', '#12f5d0', '#12f5cf', '#12f5ce', '#12f5cd', '#12f5cc', '#12f5cb', '#12f5ca', '#12f5c9', '#12f5ca', '#12f5c9', '#12f5c8', '#12f5c7', '#12f5c6', '#12f5c5', '#12f5c4', '#12f5c3', '#12f5c2', '#12f5c1', '#12f5c0', '#12f5bf', '#12f5be', '#12f5bd', '#12f5bc', '#12f5bb', '#12f5bc', '#12f5bb', '#12f5ba', '#12f5b9', '#12f5b8', '#12f5b7', '#12f5b6', '#12f5b5', '#12f5b4', '#12f5b3', '#12f5b2', '#12f5b1', '#12f5b0', '#12f5af', '#12f5ae', '#12f5ad', '#12f5ae', '#12f5ad', '#12f5ac', '#12f5ab', '#12f5aa', '#12f5a9', '#12f5a8', '#12f5a7', '#12f5a6', '#12f5a5', '#12f5a4', '#12f5a3', '#12f5a2', '#12f5a1', '#12f5a0', '#12f59f', '#12f6a0', '#12f69f', '#12f69e', '#12f69d', '#12f69c', '#12f69b', '#12f69a', '#12f699', '#12f698', '#12f697', '#12f696', '#12f695', '#12f694', '#12f693', '#12f692', '#12f691', '#12f692', '#12f691', '#12f690', '#12f68f', '#12f68e', '#12f68d', '#12f68c', '#12f68b', '#12f68a', '#12f689', '#12f688', '#12f687', '#12f686', '#12f685', '#12f684', '#12f683', '#12f684', '#12f683', '#12f682', '#12f681', '#12f680', '#12f67f', '#12f67e', '#12f67d', '#12f67c', '#12f67b', '#12f67a', '#12f679', '#12f678', '#12f677', '#12f676', '#12f675', '#12f676', '#12f675', '#12f674', '#12f673', '#12f672', '#12f671', '#12f670', '#12f66f', '#12f66e', '#12f66d', '#12f66c', '#12f66b', '#12f66a', '#12f669', '#12f668', '#12f667', '#12f668', '#12f667', '#12f666', '#12f665', '#12f664', '#12f663', '#12f662', '#12f661', '#12f660', '#12f65f', '#12f65e', '#12f65d', '#12f65c', '#12f65b', '#12f65a', '#12f659', '#12f659', '#12f658', '#12f657', '#12f656', '#12f655', '#12f654', '#12f653', '#12f652', '#12f651', '#12f650', '#12f64f', '#12f64e', '#12f64d', '#12f64c', '#12f64b', '#12f64a', '#12f64b', '#12f64a', '#12f649', '#12f648', '#12f647', '#12f646', '#12f645', '#12f644', '#12f643', '#12f642', '#12f641', '#12f640', '#12f63f', '#12f63e', '#12f63d', '#12f63c', '#12f73d', '#12f73c', '#12f73b', '#12f73a', '#12f739', '#12f738', '#12f737', '#12f736', '#12f735', '#12f734', '#12f733', '#12f732', '#12f731', '#12f730', '#12f72f', '#12f72e', '#12f72f', '#12f72e', '#12f72d', '#12f72c', '#12f72b', '#12f72a', '#12f729', '#12f728', '#12f727', '#12f726', '#12f725', '#12f724', '#12f723', '#12f722', '#12f721', '#12f720', '#12f721', '#12f720', '#12f71f', '#12f71e', '#12f71d', '#12f71c', '#12f71b', '#12f71a', '#12f719', '#12f718', '#12f717', '#12f716', '#12f715', '#12f714', '#12f713', '#12f712', '#12f712', '#13f712', '#14f712', '#15f712', '#16f712', '#17f712', '#18f712', '#19f712', '#1af712', '#1bf712', '#1cf712', '#1df712', '#1ef712', '#1ff712', '#20f712', '#21f712', '#1ff712', '#20f712', '#21f712', '#22f712', '#23f712', '#24f712', '#25f712', '#26f712', '#27f712', '#28f712', '#29f712', '#2af712', '#2bf712', '#2cf712', '#2df712', '#2ef712', '#2df712', '#2ef712', '#2ff712', '#30f712', '#31f712', '#32f712', '#33f712', '#34f712', '#35f712', '#36f712', '#37f712', '#38f712', '#39f712', '#3af712', '#3bf712', '#3cf712', '#3bf812', '#3cf812', '#3df812', '#3ef812', '#3ff812', '#40f812', '#41f812', '#42f812', '#43f812', '#44f812', '#45f812', '#46f812', '#47f812', '#48f812', '#49f812', '#4af812', '#4af812', '#4bf812', '#4cf812', '#4df812', '#4ef812', '#4ff812', '#50f812', '#51f812', '#52f812', '#53f812', '#54f812', '#55f812', '#56f812', '#57f812', '#58f812', '#59f812', '#58f812', '#59f812', '#5af812', '#5bf812', '#5cf812', '#5df812', '#5ef812', '#5ff812', '#60f812', '#61f812', '#62f812', '#63f812', '#64f812', '#65f812', '#66f812', '#67f812', '#66f812', '#67f812', '#68f812', '#69f812', '#6af812', '#6bf812', '#6cf812', '#6df812', '#6ef812', '#6ff812', '#70f812', '#71f812', '#72f812', '#73f812', '#74f812', '#75f812', '#75f812', '#76f812', '#77f812', '#78f812', '#79f812', '#7af812', '#7bf812', '#7cf812', '#7df812', '#7ef812', '#7ff812', '#80f812', '#81f812', '#82f812', '#83f812', '#84f812', '#83f812', '#84f812', '#85f812', '#86f812', '#87f812', '#88f812', '#89f812', '#8af812', '#8bf812', '#8cf812', '#8df812', '#8ef812', '#8ff812', '#90f812', '#91f812', '#92f812', '#92f912', '#93f912', '#94f912', '#95f912', '#96f912', '#97f912', '#98f912', '#99f912', '#9af912', '#9bf912', '#9cf912', '#9df912', '#9ef912', '#9ff912', '#a0f912', '#a1f912', '#a0f912', '#a1f912', '#a2f912', '#a3f912', '#a4f912', '#a5f912', '#a6f912', '#a7f912', '#a8f912', '#a9f912', '#aaf912', '#abf912', '#acf912', '#adf912', '#aef912', '#aff912', '#aff912', '#b0f912', '#b1f912', '#b2f912', '#b3f912', '#b4f912', '#b5f912', '#b6f912', '#b7f912', '#b8f912', '#b9f912', '#baf912', '#bbf912', '#bcf912', '#bdf912', '#bef912', '#bdf912', '#bef912', '#bff912', '#c0f912', '#c1f912', '#c2f912', '#c3f912', '#c4f912', '#c5f912', '#c6f912', '#c7f912', '#c8f912', '#c9f912', '#caf912', '#cbf912', '#ccf912', '#cbf912', '#ccf912', '#cdf912', '#cef912', '#cff912', '#d0f912', '#d1f912', '#d2f912', '#d3f912', '#d4f912', '#d5f912', '#d6f912', '#d7f912', '#d8f912', '#d9f912', '#daf912', '#daf912', '#dbf912', '#dcf912', '#ddf912', '#def912', '#dff912', '#e0f912', '#e1f912', '#e2f912', '#e3f912', '#e4f912', '#e5f912', '#e6f912', '#e7f912', '#e8f912', '#e9f912', '#e9f912', '#eaf912', '#ebf912', '#ecf912', '#edf912', '#eef912', '#eff912', '#f0f912', '#f1f912', '#f2f912', '#f3f912', '#f4f912', '#f5f912', '#f6f912', '#f7f912', '#f8f912', '#f7fa12', '#f7f912', '#f7f812', '#f7f712', '#f7f612', '#f7f512', '#f7f412', '#f7f312', '#f7f212', '#f7f112', '#f7f012', '#f7ef12', '#f7ee12', '#f7ed12', '#f7ec12', '#f7eb12', '#faee12', '#faed12', '#faec12', '#faeb12', '#faea12', '#fae912', '#fae812', '#fae712', '#fae612', '#fae512', '#fae412', '#fae312', '#fae212', '#fae112', '#fae012', '#fadf12', '#fae012', '#fadf12', '#fade12', '#fadd12', '#fadc12', '#fadb12', '#fada12', '#fad912', '#fad812', '#fad712', '#fad612', '#fad512', '#fad412', '#fad312', '#fad212', '#fad112', '#fad112', '#fad012', '#facf12', '#face12', '#facd12', '#facc12', '#facb12', '#faca12', '#fac912', '#fac812', '#fac712', '#fac612', '#fac512', '#fac412', '#fac312', '#fac212', '#fac312', '#fac212', '#fac112', '#fac012', '#fabf12', '#fabe12', '#fabd12', '#fabc12', '#fabb12', '#faba12', '#fab912', '#fab812', '#fab712', '#fab612', '#fab512', '#fab412', '#fab512', '#fab412', '#fab312', '#fab212', '#fab112', '#fab012', '#faaf12', '#faae12', '#faad12', '#faac12', '#faab12', '#faaa12', '#faa912', '#faa812', '#faa712', '#faa612', '#fba612', '#fba512', '#fba412', '#fba312', '#fba212', '#fba112', '#fba012', '#fb9f12', '#fb9e12', '#fb9d12', '#fb9c12', '#fb9b12', '#fb9a12', '#fb9912', '#fb9812', '#fb9712', '#fb9812', '#fb9712', '#fb9612', '#fb9512', '#fb9412', '#fb9312', '#fb9212', '#fb9112', '#fb9012', '#fb8f12', '#fb8e12', '#fb8d12', '#fb8c12', '#fb8b12', '#fb8a12', '#fb8912', '#fb8a12', '#fb8912', '#fb8812', '#fb8712', '#fb8612', '#fb8512', '#fb8412', '#fb8312', '#fb8212', '#fb8112', '#fb8012', '#fb7f12', '#fb7e12', '#fb7d12', '#fb7c12', '#fb7b12', '#fb7b12', '#fb7a12', '#fb7912', '#fb7812', '#fb7712', '#fb7612', '#fb7512', '#fb7412', '#fb7312', '#fb7212', '#fb7112', '#fb7012', '#fb6f12', '#fb6e12', '#fb6d12', '#fb6c12', '#fb6d12', '#fb6c12', '#fb6b12', '#fb6a12', '#fb6912', '#fb6812', '#fb6712', '#fb6612', '#fb6512', '#fb6412', '#fb6312', '#fb6212', '#fb6112', '#fb6012', '#fb5f12', '#fb5e12', '#fb5e12', '#fb5d12', '#fb5c12', '#fb5b12', '#fb5a12', '#fb5912', '#fb5812', '#fb5712', '#fb5612', '#fb5512', '#fb5412', '#fb5312', '#fb5212', '#fb5112', '#fb5012', '#fb4f12', '#fc5012', '#fc4f12', '#fc4e12', '#fc4d12', '#fc4c12', '#fc4b12', '#fc4a12', '#fc4912', '#fc4812', '#fc4712', '#fc4612', '#fc4512', '#fc4412', '#fc4312', '#fc4212', '#fc4112', '#fc4112', '#fc4012', '#fc3f12', '#fc3e12', '#fc3d12', '#fc3c12', '#fc3b12', '#fc3a12', '#fc3912', '#fc3812', '#fc3712', '#fc3612', '#fc3512', '#fc3412', '#fc3312', '#fc3212', '#fc3312', '#fc3212', '#fc3112', '#fc3012', '#fc2f12', '#fc2e12', '#fc2d12', '#fc2c12', '#fc2b12', '#fc2a12', '#fc2912', '#fc2812', '#fc2712', '#fc2612', '#fc2512', '#fc2412', '#fc2412', '#fc2312', '#fc2212', '#fc2112', '#fc2012', '#fc1f12', '#fc1e12', '#fc1d12', '#fc1c12', '#fc1b12', '#fc1a12', '#fc1912', '#fc1812', '#fc1712', '#fc1612', '#fc1512', '#fc1612', '#fc1613', '#fc1614', '#fc1615', '#fc1616', '#fc1617', '#fc1618', '#fc1619', '#fc161a', '#fc161b', '#fc161c', '#fc161d', '#fc161e', '#fc161f', '#fc1620', '#fc1621', '#fc121c', '#fc121d', '#fc121e', '#fc121f', '#fc1220', '#fc1221', '#fc1222', '#fc1223', '#fc1224', '#fc1225', '#fc1226', '#fc1227', '#fc1228', '#fc1229', '#fc122a', '#fc122b']

def genercolors(colors):
	for row in colors:
		yield row

def addcolor(arg):
	color = next(colorgen)
	arg['COLORKEY'] = color
	return arg

# makes a individual colorkey field for each unique value in categorical data
# assumes your maximum number of fields is currently under 51
def unique_groupby(data,field):
	global colorgen

	global colors
	colors = get_heatmaplarge()
	colors = reduce_color_list_size(np.unique(data[field]).tolist()+['end'],colors)
	colorgen = genercolors(colors)



	df = data.groupby(field).apply(addcolor)
	return df


# making unique object for a fields range values 
def make_object_map(data,field,**kwargs):
	linear = False
	for key,value in kwargs.iteritems():
		if key == 'linear':
			linear = value
	print linear
	if linear == False:
		colors,rangelist = make_distributed_range(data,field)
	else:
		colors = get_heatmap51()
		colors2 = colors 
		maxvalue = data[field].max()
		if maxvalue < 51:
			totallist = range(maxvalue)
			colors = reduce_color_list_size(totallist,colors)
			colors,rangelist = make_gradient_range(data[field].min(),maxvalue,colors)
		else:
			colors = reduce_color_list_size(range(len(data)),colors)
			colors,rangelist = make_gradient_range(data[field].min(),maxvalue,colors)
			if not rangelist[0] == 0:
				rangelist = [0] + rangelist[1:]
			data['COLORKEY'] = pd.cut(data[field],bins=rangelist+[1000000000],labels=colors)
			
			return data
	colors2 = get_heatmap51()
	if not rangelist[0] == 0:
		rangelist = [0] + rangelist[1:]
	data['COLORKEY'] = pd.cut(data[field],bins=rangelist,labels=colors[1:])
	
	return data

# for a given dataframe and field returns a non used grouped object to multiple operations on 
def make_group(data,field):
	return data.groupby(field)

# assemble dummy values for specific uniques in a column field
# then appends or joins to existing df
# options assumes a categorical field is being added 
# and therefor will perform operations on outer fields like average percentage of max,
# basically stuff that pipegeohash will use
# wont expanding out options until i find out what options it should have 
def assemble_dummies(data,column,uniques,**kwargs):
	options = False
	for key,value in kwargs.iteritems():
		if key == 'options':
			options = value
	
	uniquelist = []
	for row in uniques:
		row = str(column) + '-' + str(row)
		uniquelist.append(row)

 	data[uniquelist] = pd.get_dummies(data,columns=[column],prefix_sep='-')[uniquelist]
 	return data

