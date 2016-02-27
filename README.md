### berrl - MapBox map output made simple with Python data structures
![](https://cloud.githubusercontent.com/assets/10904982/13199289/86ce2388-d7ef-11e5-856e-731d8212d2b4.png)
![](https://cloud.githubusercontent.com/assets/10904982/13324091/44110fd8-dbaa-11e5-97d1-414d48a4f787.png)

#### What is it?
This repository is a combination of 3 repositories I've previously made for geospatial data analysis. These modules I often found myself using in conjuction with one another and figured it would be useful to make an intuitive all in one repository to take full advantage and simplify the work I've already done. The general premise is keep things static enough to where pandas data structures can be integrated in a simple and intuitive manner by making some general assumptions about how the data will be inputted. The main asssumptions being: all geospatial fields will contain 'LAT','LONG', or 'ELEV' for their representive geo fields, and assuming that points and blocks (geohashed squares) can be input in multiples (i.e. each row is 1 element) and that polygons and linestrings are input one element at a time but still in tabular style. 

Instead of using functions made for JS and ported to Python I do the reverse making pandas dataframes able to be directly input and parsed correctly into geojson and styled generally how I desire it.By doing this one can put the geospatial analysis on the shoulders of pandas and numpy and put a lot of the hang ups when dealing with geospatial data to the side or at least make them static enough to negate a lot of the confusion. 

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

#### Setup and Usage Notes
To setup currently download this repository navigate to it and enter the following in terminal:
```
python setup.py install
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
![](https://cloud.githubusercontent.com/assets/10904982/13198501/0da25ffe-d7d8-11e5-870c-ebef73bdfd1d.png)

#### A little more Advanced Example
Say we want to iterate through all unique values in a field and style them a certain way based on each unique value in said field. We also only want the most dense areas of shark attacks to map and also want to display the squares in which these densities reside. We could do this pretty easily using berrl. 

**NOTE: that unique values outnumbered unique colors (at least currently) so not all activities were iterated through this is mainly just an example of what you could do.**

```python
import berrl as bl
import pandas as pd
import numpy as np
import itertools

apikey='your api key'

# all the colors currently available for input
colors=['default','light green', 'blue', 'red', 'yellow', 'light blue', 'orange', 'purple', 'green', 'brown', 'pink']

# reading csv file to pandas
data=pd.read_csv('sharks.csv')

# mapping table to precision 4 geohashs
data=bl.map_table(data,3,list=True) # this creates a csv file with a density block table
squares=pd.read_csv('squares3.csv')
squares=squares[:10] # getting the top 10 densest geohash squares

# getting each unique geohash
geohashs=np.unique(squares['GEOHASH']).tolist()

# constructing list of all top shark attack incidents
total=[data.columns.values.tolist()]
for row in geohashs:
	temp=data[data.GEOHASH==str(row)] # getting all the geohashs within the entire table
	temp=bl.df2list(temp) # taking dataframe to list
	total+=temp[1:] #ignoring the header on each temporary list


# taking list back to dataframe
total=bl.list2df(total)

# getting the unique activities that occured
uniques=np.unique(total['Activity']).tolist()

# we now have a list with each top geohash in a aggregated table
# we can now style each color icon based on each activity being performed during the attack
count=0
filenames=[]
for unique,color in itertools.izip(uniques,colors):
	count+=1
	filename=str(count)+'.geojson' # generating a dummy file name
	temp=total[total.Activity==unique] 
	if not len(temp)==0: # if dataframe is empty will not make_points
		temp['color']=str(color) # setting specific color to object
		a=bl.make_points(temp,list=True) # making geojson object 
		bl.parselist(a,filename) # writing object to file
		filenames.append(filename)

# writing the squares table and setting color to red
squares['color']='red'
a=bl.make_blocks(squares,list=True)
bl.parselist(a,'squares.geojson')

# adding squares to filenames
filenames.append('squares.geojson')

#loading final html
bl.loadparsehtml(filenames,apikey,colorkey='color')
```

##### Output Map Below
![](https://cloud.githubusercontent.com/assets/10904982/13198831/795c37a2-d7e1-11e5-9733-584f3f544831.png)
![](https://cloud.githubusercontent.com/assets/10904982/13198832/7c66f176-d7e1-11e5-986d-0da285c97cc1.png)

```
BERRL DOCUMENTATION
 A. PIPEGEOJSON
 B. PIPEGEOHASH
 C. PIPEHTML

A. PIPEGEOJSON 
This section of the documentation contains functions for creating geojson features.
Its important to note that square and polygon functions accept one table representing the alignment of an element while blocks and points accept tables with each row representing an individual element

GEOJSON CREATION
 1) Single element creation
  make_line(table,**kwargs)
  make_polygon(table,**kwargs)
 2) Multiple Element functions 
  make_points(table,**kwargs)
  make_blocks(table,**kwargs)
 3) MISC.
  parselist(lines,filelocation)

	1) Single Element Functions Operating over an alignment.
These functions take list of elements representing 

1) Single element creation
These functions one alignment of an element in tabular format.

function: make_line(table,**kwargs):
	table: where it can be either a csvfile location, a pandas dataframe, or a regular list, the table represent one element A csv file location is the default assumption

		** list: boolean where if your using it your sending in “list=True” to indicate your are sending in an object already read into memory

function: make_polygon(table,**kwargs):
	table: where it can be either a csvfile location, a pandas dataframe, or a regular list, the table represent one element. A cvs file location is the default assumption

		** list: boolean where if your using it your sending in “list=True” to indicate your are sending in an object already read into memory


	2) Multiple Element functions 
These functions either accept a row representing 4 points with 8 columns representing 
each corner of the block. The make_block() function was made to be used directly with the pipegeohash’s map_table() function output csv table.

function: make_points(table,**kwargs):
	table: where it can be either a csvfile location, a pandas dataframe, or a regular list, the table represents a point in every row

function: make_blocks(table,**kwargs):
	table: where it can be either a csvfile location, a pandas dataframe, or a regular list, the table represents a blocks in every row typically expected to be like the output of the one in the pipegeohash map_table() algorithm a cvs file location is the default assumption

		** list: boolean where if your using it your sending in “list=True” to indicate your are sending in an object already read into memory

	3) MISC.
Miscellaneous functions you might need when using this module.

function parselist(lines,filelocation):
	lines: this is the output of any make_ function above it returns the list of lines to be written into a txt file,

	filelocation: the file location to be written to, typically written with a geojson extension hopefully may add something to raise an exception if it doesn’t have one

B. PIPEGEOHASH
PIPEGEOHASH in my opinion is one the most useful modules because it helps with so many things that already are often done already and make certain algorithms worlds easier.It can be described as a block association and reduction in list. Geohashing uses a hierarchal rounding based approach to lat/longs reducing a decimal place per tier. This makes floating point data thats typically hard to derive associate value from associative, enormously valuable. 

If you deal with the structure like I use in the make_functions for your data any structure or table can utilize the map_table function(). This central function takes the input table finds the lat and long fields puts them into a geohashing function and a field of x geohash precision to the table and returning it. While were mapping this table it automatically assumes you want it reduced by its unique keys and outputs a table with the geohash, 4 point coordinates (8 fields) and the count occurring in each geohash. 

A great use case thats not so obvious for PIPEGEOHASH is gathering an incident about an alignment or having an alignment and needing to get only incidents occurring on it like a roadway, Say we have one route and a list of points representing car crashs, to find the incidents along the route map_table() on the table representing a roadway alignment and map_table() for the points table as well; imagine it as paints a window along an alignment in which you can very your sensivity but usually pretty high like 7,8. We can apply the np.unique(dataframe[‘GEOHASH’]).tolist() directly to our mapped tables to get the unique values in each.  We have a list of unique hash values we want to know points are on and a set of points to iterate through if they share any there along the road. A pretty familiar list comprehension. 


PIPEGEOHASH
 1) MAIN OPERATION OF FUNCTION THE GEOHASHING AND REDUCTION
  map_table(table,precision,**kwargs)

	1) MAIN OPERATION OF FUNCTION THE GEOHASHING AND REDUCTION
function map_table(table,precision,**kwargs):
	
	table: where it can be either a csvfile location, a pandas dataframe, or a regular list, the table represent one element A cvs file location is the default assumption,
	
	precision: A int value value 1 to 8 for the size of the GEOHASH square to use,
		
		** list: boolean where if your using it your sending in “list=True” to indicate your are sending in an object already read into memory

C. PIPEHTML
This module is meant to use parse and open the JavaScript/HTML used for this map. I add a popup menu for all elements loaded via GeoJSON bringing in element header/features to the popup icon but often times they are to large without a iframe, iframe that and making it a legitimate HTML table is one of the things on the list. This module also contains the realtime script for PIPEHTML as well

PIPEHTML
 1) PIPEHTML
  loadparsehtml(filenames,apikey,**kwargs)
 2) PIPEREALTIME
  loadparsehtmlrealtime(filenames,apices,**kwargs)
 3) MISC.
  collect()
  show()

**This operation requires a localhost at your directory to serve GeoJSONs**

How to start a localhost http server:
 1) Navigate to the directory that your executing from
 2) in terminal “python -m SimpleHTTPServer”
	
	1) PIPEHTML
PARSES and opens html document automatically **currently uses Safari due localhost restriction can be turned off ‘Developer>Disable Local File Restrictions’. Currently features regarding functionality are extremely limited when it comes to styling, but can input colors and automatically generates data associated with elment (and opening it)

function loadparsehtml(filenames,apikey,**kwargs)
	filenames: a list of geojson file locations you wish to be parsed/loaded into the html, if you like to live dangerously you can always use the collect() function which collects all the geojson file locations/folders in the current file directory,
	
	apikey: the MapBox api key,

		** frame: boolean value that if your using it input frame=True and then returns the html/url in a string link instead of simply opening the created html document and opening it, use this for integration with Jupyter notebooks and then use show() of the output of this functions to output the map in an iFrame in Jupyter,

		** colorkey: to indicate a color for each geojson feature simply add a color column in DataFrame indicating the color of the object (see below for currently applicable colors) the colorkey is that columns header value so usually for colorkey=‘color’ just because I call my color indication column color

	2) PIPEREALTIME
The same thing as PIPEHTML but reloads the geojson locations over a given time series or by default every 2 seconds. Currently only supports 1 time series for every geojson but eventually we’ll support variable timing based on the elements

function loadparsehtml(filenames,apikey,**kwargs)
	filenames: a list of geojson file locations you wish to be parsed/loaded into the html, if you like to live dangerously you can always use the collect() function which collects all the geojson file locations/folders in the current file directory,
	
	apikey: the MapBox api key,

		** frame: boolean value that if your using it input frame=True and then returns the html/url in a string link instead of simply opening the created html document and opening it, use this for integration with Jupyter notebooks and then use show() of the output of this functions to output the map in an iFrame in Jupyter,

		** colorkey: to indicate a color for each geojson feature simply add a color column in DataFrame indicating the color of the object (see below for currently applicable colors) the colorkey is that columns header value so usually for colorkey=‘color’ just because I call my color indication column color
	
		** time: the time series interval in milliseconds that you want the geojsons to be updated at

	3) MISC.
Miscellaneous functions you might need when using this module.

function collect():
	No arguments: Collects all the geojson locations from the current directory used for when you want to load all the geojson files written into the current directory 

function show(html): 
	html: the output of loadparsehtml() or loadparsehtmlrealtime() when using frame=True kwarg to output the iFrame of the map in Jupyter
```
