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

