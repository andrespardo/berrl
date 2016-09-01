import psycopg2
import pandas as pd
import sys
import itertools
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

def retrieve_buffer(conn,dbname,SID,geomcolumn):
	cur = conn.cursor('cursor-name')
	cur.itersize = 1000
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
		string = "SELECT *,ST_AsEWKT(ST_Transform(%s,%s)) FROM %s LIMIT %s;" % (geomcolumn,SID,dbname,100000)
	
	
	cur.execute(string)
	data = cur.fetchall()
	cur.close()

	return data,conn
	


def get_header(conn,dbname):
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
def get_both2(conn,dbname,SID):
	header = get_header(conn,dbname)
	for row in header:
		if 'geom' in str(row):
			geometryheader = row
	data,conn = retrieve_buffer(conn,dbname,SID,geometryheader)
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
	for key,value in kwargs.iteritems():
		if key == 'conn':
			conn = value
	SID=4326
	# dbname is the database name
	# SID is the spatial identifier you wish to output your table as usually 4326
	if kwargs is not None:
		for key,value in kwargs.iteritems():
			if key == 'SID':
				SID = int(value)
	if conn == False:
		conn = connect_to_db(dbname)
	
	data,conn = get_both2(conn,dbname,SID)
	return data,conn
