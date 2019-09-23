#!/usr/bin/python3

import psycopg2
import re
import string
import sys
from psycopg2 import sql

_PUNCTUATION = frozenset(string.punctuation)

def _remove_punc(token):
	"""Removes punctuation from start/end of token."""
	i = 0
	j = len(token) - 1
	idone = False
	jdone = False
	while i <= j and not (idone and jdone):
		if token[i] in _PUNCTUATION and not idone:
			i += 1
		else:
			idone = True
		if token[j] in _PUNCTUATION and not jdone:
			j -= 1
		else:
			jdone = True
	return "" if i > j else token[i:(j+1)]

def _get_tokens(query):
	rewritten_query = []
	nonrepeated_query = []
	tokens = re.split('[ \n\r]+', query)
	for token in tokens:
		cleaned_token = _remove_punc(token)
		if cleaned_token:
			if "'" in cleaned_token:
				cleaned_token = cleaned_token.replace("'", "''")
			rewritten_query.append(cleaned_token)
	#Remove duplicates
	nonrepeated_query = list(set(rewritten_query))
	return nonrepeated_query



def search(query, query_type, page_num):
    # Retrieve the cleaned query
	rewritten_query = _get_tokens(query)
	# Don't bother querying something if nothing was passed in
	if len(rewritten_query) == 0:
		return []

	connection = None
	cursor = None
	rows = []
	sign = None
	total_rows = None
	
	# Format the template as needed
	num_match = len(rewritten_query)
	if query_type == 'or':
		num_match = 1
		sign = '>='
	elif query_type == 'and':
		sign = '='
	else:
		print("Invalid query type, choose \'and\' or \'or\'")
		return []
		
	# Notice that we are still protected from sql injection even though we use the % operator on these
	# two parts of the query template, since we don't really take user's raw input into account when merging
	query_template1 = """
		DROP MATERIALIZED VIEW IF EXISTS query_result;
		CREATE MATERIALIZED VIEW query_result AS
		SELECT
			s.song_name,
			a.artist_name,
			s.page_link,
			SUM(score) as total
		FROM
			tfidf t
		INNER JOIN song s ON t.song_id = s.song_id
		INNER JOIN artist a ON a.artist_id = s.artist_id
		WHERE token in (%s)""" % ', '.join(['%s'] * len(rewritten_query))
		
	query_template2 = """
		GROUP BY s.song_id, a.artist_name, s.page_link
		HAVING COUNT(*) %s %d
		ORDER BY total DESC;
	""" % (sign, num_match)
	
	query_template = query_template1 + query_template2
	
	select_template = """
		SELECT * 
		FROM query_result
		LIMIT 20
		OFFSET %d;
	""" % ((page_num - 1) * 20)
	
	try:
		# Attempt to connect to local database and query
		connection = psycopg2.connect(user = "cs143", password = "cs143", host = "localhost", port = "5432", database = "searchengine")
        
		cursor = connection.cursor()
		if page_num == 1:
			cursor.execute(query_template, tuple(rewritten_query))
		cursor.execute(select_template)
		rows = cursor.fetchall()
		
		cursor.execute("SELECT COUNT(*) FROM query_result;")
		rows.append(cursor.fetchall()[0])
		
		# Have to commit the connection for some reason
		connection.commit()
	except (Exception, psycopg2.Error) as error:
		print("Error connecting to Search Engine database")
		if (connection):
			cursor.close()
			connection.close()
	finally:
		if (connection):
			cursor.close()
			connection.close()
	return rows

if __name__ == "__main__":
	if len(sys.argv) > 2:
		result = search(' '.join(sys.argv[2:]), sys.argv[1].lower(), 1)
		del result[-1]
		for row in result:
			print(row)
	else:
		print("USAGE: python3 search.py [or|and] term1 term2 ...")
