import berrl as bl
import numpy as np
import pandas as pd

key='pk.eyJ1IjoibXVycGh5MjE0IiwiYSI6ImNpam5kb3puZzAwZ2l0aG01ZW1uMTRjbnoifQ.5Znb4MArp7v3Wwrn6WFE6A'

# reading into memory
points=pd.read_csv('points_example.csv')
line=pd.read_csv('line_example.csv')

# geohashing each table
points=bl.map_table(points,7,list=True)
line=bl.map_table(line,7,list=True)

# getting unique geohashs 
uniquepoints=np.unique(points['GEOHASH']).tolist()
uniqueline=np.unique(line['GEOHASH']).tolist()

newpoints=[points.columns.values.tolist()]
# we know if a unique point is in any unique line its on the route
for row in uniquepoints:
	oldrow=row
	for row in uniqueline:
		if row==oldrow:
			temp=points[points.GEOHASH==oldrow]
			temp=bl.df2list(temp)
			newpoints+=temp[1:] # getting all the points within this geohashs

# making the new points, line, and blocks along line 
bl.make_points(newpoints,list=True,filename='points.geojson')
bl.make_blocks('squares7.csv',filename='blocks_on_line.geojson')
bl.make_line(line,list=True,filename='line.geojson')


bl.loadparsehtml(bl.collect(),key)