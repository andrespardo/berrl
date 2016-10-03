import psycopg2
import pandas as pd
import sys
import itertools
from sqlalchemy import create_engine

'''
Purpose: This module exists as an easy postgis integration module its purpose is to
bring in database in its entirety into memory in the future in may support more robust querries
but for now only supports getting an entire database into memory 

Currently only supports input databases with no passwords. Its currently meant to be used for postgis
polygons and linestrings, in the future may also support point data. 

Created by: Bennett Murphy
'''

# intially connects to database
def connect_to_db(dbname):
	string = "dbname=%s user=postgres password=secret" % (dbname)
 	try:
 		conn = psycopg2.connect(string)
 	except Exception:
 		print 'failed connection'
 	return conn


def retrieve(conn,dbname,SID,geomcolumn):
	DEC2FLOAT = psycopg2.extensions.new_type(
    	psycopg2.extensions.DECIMAL.values,
    	'DEC2FLOAT',
    	lambda value, curs: float(value) if value is not None else None)
	psycopg2.extensions.register_type(DEC2FLOAT)
	if SID==0:
		string = "SELECT *,ST_AsEWKT(%s) FROM %s;" % (geomcolumn,dbname)
		'''
		elif SID==10000:
			string = """""SELECT gid, ST_AsEWKT(ST_Collect(ST_MakePolygon(geom))) As geom FROM(SELECT gid, ST_ExteriorRing((ST_Dump(geom)).geom) As geom FROM %s)s GROUP BY gid; """"" % (dbname)
		'''
	else:
		string = "SELECT *,ST_AsEWKT(ST_Transform(%s,%s)) FROM %s;" % (geomcolumn,SID,dbname)
	cur = conn.cursor()

	try:
		cur.execute(string)
	except psycopg2.Error as e:
		print 'failed'

	data = cur.fetchall()
	return data


# returns an engine and an sql querry 
# to be sent into read_sql querry
# regular_db is bool kwarg for whether 
# the dbname your querry is to return geometries
def make_query(dbname,**kwargs):
	regular_db = False
	tablename = False
	for key,value in kwargs.iteritems():
		if key == 'regular_db':
			regular_db = value
		if key == 'tablename':
			tablename = value

	# getting appropriate sql querry
	if regular_db == False:
		if tablename == False:
			try:
				sqlquerry = "SELECT *,ST_AsEWKT(ST_Transform(geom,4326)) FROM %s" % dbname
			except:
				sqlquerry = "SELECT * FROM %s" % dbname
		else:

			sqlquerry = "SELECT * FROM %s" % tablename

	else:
		if tablename == False:
			sqlquerry = "SELECT * FROM %s" % dbname
		else:
			sqlquerry = "SELECT * FROM %s" % tablename

	# creating engine using sqlalchemy
	engine = create_engine('postgresql://postgres:pass@localhost/%s' % dbname)

	return sqlquerry,engine


# creating simpoly an engine for a given 
def create_sql_engine(dbname):
	return create_engine('postgresql://postgres:pass@localhost/%s')

def retrieve_buffer(conn,dbname,args,geomcolumn):
	#unpacking arguments 
	SID,size,normal_db,tablename = args
	if not tablename == False:
		dbname = tablename

	cur = conn.cursor('cursor-name')
	cur.itersize = 1000
	if size == False:
		size = 100000
	DEC2FLOAT = psycopg2.extensions.new_type(
    	psycopg2.extensions.DECIMAL.values,
    	'DEC2FLOAT',
    	lambda value, curs: float(value) if value is not None else None)
	psycopg2.extensions.register_type(DEC2FLOAT)
	

	if SID==0:
		string = "SELECT *,ST_AsEWKT(%s) FROM %s;" % (geomcolumn,dbname)
		'''
		elif SID==10000:
			string = """""SELECT gid, ST_AsEWKT(ST_Collect(ST_MakePolygon(geom))) As geom FROM(SELECT gid, ST_ExteriorRing((ST_Dump(geom)).geom) As geom FROM %s)s GROUP BY gid; """"" % (dbname)
		'''
	else:
		if normal_db == False:
			string = "SELECT *,ST_AsEWKT(ST_Transform(%s,%s)) FROM %s LIMIT %s;" % (geomcolumn,SID,dbname,size)
		else:
			string = "SELECT * FROM %s LIMIT %s;" % (dbname,size)

	cur.execute(string)
	data = cur.fetchall()
	cur.close()

	return data,conn
	


def get_header(conn,dbname,normal_db):
	cur = conn.cursor()
	string = "SELECT a.attname as column_name, format_type(a.atttypid, a.atttypmod) AS data_type FROM pg_attribute a JOIN pg_class b ON (a.attrelid = b.relfilenode) WHERE b.relname = '%s' and a.attstattarget = -1;" % (dbname)
	try:
		cur.execute(string)
	except psycopg2.Error as e:
		print 'failed'
	header = cur.fetchall()
	newheader = []
	for row in header:
		newheader.append(row[0])
	if normal_db == False:
		newheader.append('st_asewkt')
	return newheader

# takes a list and turns it into a datafrae
def list2df(df):
    df = pd.DataFrame(df[1:], columns=df[0])
    return df

# takes a dataframe and turns it into a list
def df2list(df):
    df = [df.columns.values.tolist()]+df.values.tolist()
    return df

# gets both column header and data 
def get_both(conn,dbname,SID):	
	header = get_header(conn,dbname)
	for row in header:
		if 'geom' in str(row):
			geometryheader = row
	data = retrieve(conn,dbname,SID,geometryheader)
	data = pd.DataFrame(data,columns=header)
	return data

# gets both column header and data 
def get_both2(conn,dbname,args):
	a,b,normal_db,tablename = args
	if not tablename == False:
		header = get_header(conn,tablename,normal_db)
	else:
		header = get_header(conn,dbname,normal_db)

	geometryheader = False
	for row in header:
		if 'geom' in str(row):
			geometryheader = row

	data,conn = retrieve_buffer(conn,dbname,args,geometryheader)
	data = pd.DataFrame(data,columns=header)
	return data,conn

# gets database assuming you have postgres sql server running, returns dataframe
def get_database(dbname,**kwargs):
	SID=4326
	# dbname is the database name
	# SID is the spatial identifier you wish to output your table as usually 4326
	if kwargs is not None:
		for key,value in kwargs.iteritems():
			if key == 'SID':
				SID = int(value)

	conn = connect_to_db(dbname)
	data = get_both(conn,dbname,SID)
	return data

# gets database assuming you have postgres sql server running, returns dataframe
def get_database_buffer(dbname,**kwargs):
	conn = False
	size = False
	normal_db = False
	tablename = False
	for key,value in kwargs.iteritems():
		if key == 'conn':
			conn = value
		if key == 'size':
			size = value
		if key == 'normal_db':
			normal_db = value
		if key == 'tablename':
			tablename = value
	SID=4326
	print size
	# dbname is the database name
	# SID is the spatial identifier you wish to output your table as usually 4326
	if kwargs is not None:
		for key,value in kwargs.iteritems():
			if key == 'SID':
				SID = int(value)
	if conn == False:
		conn = connect_to_db(dbname)
	
	# putting args in list so i dont have to carry through for no reason
	args = [SID,size,normal_db,tablename]

	data,conn = get_both2(conn,dbname,args)
	return data,conn

def db_buffer(dbname,**kwargs):	
	conn = False
	size = False
	normal_db = False
	tablename = False
	size = 100000
	for key,value in kwargs.iteritems():
		if key == 'conn':
			conn = value
		if key == 'size':
			size = value
		if key == 'normal_db':
			normal_db = value
		if key == 'tablename':
			tablename = value
	count = 0
	total = 0
	while size == size:
		if count == 0:
			data,conn = get_database_buffer(dbname,tablename=tablename,normal_db=normal_db,size=size)
		else:
			data,conn = get_database_buffer(dbname,tablename=tablename,normal_db=normal_db,size=size,conn=conn)
		itersize = len(data)
		total += itersize
		print 'Blocks Generated: %s,Total Rows Generated: %s' % (count,total)
		count += 1
		yield data

# generates a querry for a given lists of indexs
# reads the sql into pandas and returns result
# indexs are expected to be in string format
def select_fromindexs(dbname,field,indexs,**kwargs):
	normal_db = False
	tablename = False

	# handling even if indexs arent in str format
	if type(indexs[0]) == int:
		indexs = [str(row) for row in indexs]

	for key,value in kwargs.iteritems():
		if key == 'size':
			size = value
		if key == 'normal_db':
			normal_db = value
		if key == 'tablename':
			tablename = value
	a,engine = make_query(dbname,tablename=tablename,normal_db=normal_db)
	
	stringindexs = ','.join(indexs)

	if not tablename == False:
		dbname = tablename

	# now making querry
	query = '''SELECT * FROM %s WHERE %s IN (%s);''' % (dbname,field,stringindexs)

	return pd.read_sql_query(query,engine)
