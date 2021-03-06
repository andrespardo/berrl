### berrl - MapBox map output made simple with Python data structures
![](https://cloud.githubusercontent.com/assets/10904982/13395720/9b331588-debe-11e5-9b71-cb8d09c8684c.png)

#### What is it?
This repository is a combination of 3 repositories I've previously made for geospatial data analysis. These modules I often found myself using in conjuction with one another and figured it would be useful to make an intuitive all in one repository to take full advantage and simplify the work I've already done. The general premise is keep things static enough to where pandas data structures can be integrated in a simple and intuitive manner by making some general assumptions about how the data will be inputted. The main asssumptions being: all geospatial fields will contain 'LAT','LONG', or 'ELEV' for their representive geo fields, and assuming that points and blocks (geohashed squares) can be input in multiples (i.e. each row is 1 element) and that polygons and linestrings are input one element at a time but still in tabular style. 

Instead of using functions made for JS and ported to Python I do the reverse making pandas dataframes able to be directly input and parsed correctly into geojson and styled generally how I desire it.By doing this one can put the geospatial analysis on the shoulders of pandas and numpy and put a lot of the hang ups when dealing with geospatial data to the side or at least make them static enough to negate a lot of the confusion. 

**The result is a more stable, manageable system, that is ready for data to be dealt with in realtime, which pretty cool.**
##### Realtime mapping of Buses in LA
<p align="center">
  <img src="https://cloud.githubusercontent.com/assets/10904982/13334258/1edaf6be-dbd9-11e5-9484-2a6aaa17e0db.gif" alt="Realtime Data"/>
</p>

#### HTML/JavaScript side of mapping?
Collecting all the geojson locations as you make them and inputting a color field kwarg allows you to style/pipe data into the correct HTML by simply "peaking" into the geojsons fields and outputting the correct HTML for each individual geojson. So essentially by keeping things static we can parse the HTML into working maps pretty easily and reliably. 

The 3 modules include:
* [pipegeohash](https://github.com/murphy214/pipegeohash) - A table operation for geohashing then a groupby operation at the end (useful for a lot of algorithms and clustering)
* [pipegeojson](https://github.com/murphy214/pipegeojson) - A csv/list/dataframe to geojson parser that uses the assumptions listed above to allow styling from fields in a dataframe column
* [pipehtml](https://github.com/murphy214/pipehtml) - A module that parses the html/JavaScript for all given geojson locations peaking into the geojson to style the pop-up icon in a manner I generally desire

#### Short Videos I think show some cool Features
* [Live Realtime Mapping Points](https://www.youtube.com/watch?v=edbpT9GZ9b0)
* [Live Realtime Mapping Linestring](https://www.youtube.com/watch?v=39VFWERpMg8)
* [Heatmapping Over a Time Series Using Spark](https://www.youtube.com/watch?v=ZHf2gGxXLhc)
* [Dynamic Line Styling over Time based on speed](https://www.youtube.com/watch?v=uG_rMjy-W7I)
* [38 minutes of LA Bus Traffic in Realtime](https://www.youtube.com/watch?v=Vm-W137QhkE)

#### Setup and Usage Notes
To install berrl in terminial enter:
```
pip install berrl
```
Prereqs include:
* [geohash](https://github.com/hkwi/python-geohash) (which I think requires XCode this isn't my module just the one I used for the pipegeohash module)
* pandas/numpy

##### Usage Notes
To use berrl the way its currently implemented I recommend using Safari due to being the easiest to use local http references and on the safari bar navigate to "Develop>Disable Local File Restrictions" to allow for local file references. 

As you might have guessed this means you will have to setup a local http server which luckily isn't hard just navigate to the correct directory in terminal that you will be executing your script in and start the HTTP server with the following command in terminal:
```
python -m SimpleHTTPServer
```

Then you should be ready to Map!

#### Simple Example of berrl
Below shows an example of berrl thats is about as simple as I can make it taking a csv file of shark attacks and turning it into geojson parsing and loading the appropriate HTML

```python
import berrl as bl

apikey='your api key'

a=bl.make_points('sharks.csv')
bl.parselist(a,'sharks.geojson') # simply writes a list of lines to file name location

bl.loadparsehtml(['sharks.geojson'],apikey)
```

##### Output of Map Below
![](https://cloud.githubusercontent.com/assets/10904982/13379890/e24ec73c-de00-11e5-9ebf-ef7028553d64.png)

#### Example: Berrl for Problem Reduction
One of the main annoyances of geospatial data is it can be nasty to work with so many floating points numbers and develop reliable fast algorithms doing so. A common example of a problem like this is getting the occurances of points from a set that occur on a certain route. Here I'll first start by loading the points file and line file to visualize the problem. 
```python
import berrl as bl
import numpy as np
import pandas as pd

key='your api key'

line=pd.read_csv('line_example.csv')
points=pd.read_csv('points_example.csv')

# makes the file if given the kwarg filename for any make function
bl.make_line(line,list=True,filename='line.geojson')
bl.make_points(points,list=True,filename='points.geojson')

bl.loadparsehtml(bl.collect(),key) # collects all the geojsons that exist in the current directory 
```

##### Output of Map Below
![](https://cloud.githubusercontent.com/assets/10904982/13375628/e002668e-dd72-11e5-8b12-25191003e906.png)

##### Turning the Problem into One were familiar with
The code below shows how just a few steps with map_table() function can turn a problem like this into a simple list comprehension and shows you the blocks were iterating through to help you visualize whats going on. Were sort of windowing through blocks on the line instead of all points to simplify the problem.
```python
import berrl as bl
import numpy as np
import pandas as pd

key='your api key'

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

# loading html
bl.loadparsehtml(bl.collect(),key)
```
##### Output of Map Below 
![](https://cloud.githubusercontent.com/assets/10904982/13375726/680e642c-dd75-11e5-9086-a998ccb48cd9.png)

##### View the Documentation
**View the Documentation [here](https://raw.githubusercontent.com/murphy214/berrl/master/documentation.txt)**


#### Berrl's Structure
Berrl's strength is its sparse structure. Berrl has 4 main functions for geojson creation:
* make_line(table,**kwargs)
* make_polygon(table,**kwargs)
* make_points(table,**kwargs) ''notice the s's!''
* make_blocks(table,**kwargs) ''notice the s's!''

By default all these make_ functions assume your inputting a csv file, if not and its a list/dataframe input the kwarg "list=True". These functions by default return a list of lines to be written to a geojson file. However if you wish to write out the geojson file on the spot the kwarg for the filename location is "filename" so simply set filename equal to wherever you wish to write out the geojson.

If you understand above and the next sentence you understand berrl: **lines and polygons are assumed to be 1 element per geojson/dataframe, while blocks and points are assumed to represent multiple elements per dataframe/geojson. Generally speaking blocks are usually the output of pipegeohash. 

##### Pipegeohash
Pipegeohash is basically a way of working with vector tile sets most mapping platforms don't want you to have or don't think you would understand.(seriously) This is the foundation for a lot of mapping services and a core component in problem reduction for geospatial algorithms. However its simple in approach and implementation, it is a defined set of hierical squares on earth that can be rounded to the nearest digit and hashed into a unique string. There are 8 tiers each string from of the hash getting 1 character longer each tier and incorporating its parent hash's in all but last digit. Your taking what would be a two dimmensional block of points point numbers and turning it into a single line string representation of that square. By doing this your giving points that had no awareness of neighors around them a field to pivot and group by. 

Since I'm not serving any tiles, I don't care what you do. I use this ALL the time. Right now I'm currently tweaking with some cool geofencing algorithms that could completely turn it (geofencing) into a scalable list iteration. My module pipegeohash basically consists of one function map_table(table,precision,kwargs). It does two things a table operation on the input table for geohashing adding a field, then it groupsby geohashs and gets the block points (4 corners) yielding a table with every block in a input and the count each occurence in a block it returns the mapped table and does nothing with squares csv file. More often then not I'll end up using it somewhere down the script.

**TL:DR If your doing a lot of decimal distance calculations followed by distance querries try this module out. You could turn a nightmare into a tutorial list comphension**

##### Pipehtml/Piperealtime
Pipehtml/piperealtime have been explained quite extensively the functions however have not.
* loadparsehtml(geojsons,apikey,**kwargs)
 * geojsons is a list of geojson elements in the current directory to be loaded can also use collect() function
 * apikey is the mapbox apikey
 * **colorkey is the field in all dataframes that represents the color to be styled
 * **file_dictionary dictionary with syntax {filename:color} for all geojsons with a unique style
* loadparsehtmlrealtime(geojsons,apikey,**kwargs)
 * **kwargs can accept time interval to refresh geojsons by default 2 seconds. 

##### How to use Berrl 
Berrl's strength lies more in its simplicity then its complexity. Berrl allows you to make geojson elements, you either collect them in a list or use the collect() function to open up every geojson file in the directory and it automatically parses the JS/HTML so that element features are inserted into the popup window. Berrl also allows for a few more things abstractions from this, for example to style by color for each geojson element you have two options. 

#### Recent Updates
* postgis output integration using make_postgis_lines/make_postgis_polygons
* colorkey kwarg for styling features via a field containing a hexidecimal color
* pipewidgets - ipywidgets integration with styling updates fired upon a change in widget
* spark integration/abstractions for writing out/loading large datasets
* several useful quickmaps abstractions map for dynamically styling colors based on feature values
* merged pipehtml/piperealtime into the same module
* pipehtml now simply accepts a time kwarg if realtime interative updates are desired

