#!/usr/bin/python3

from flask import Flask, render_template, request

import search

application = app = Flask(__name__)
app.debug = True

@app.route('/search/', methods=["GET"])
def dosearch():
	query = request.args['query']
	qtype = request.args['query_type']
	page_num = int(request.args['page_num'])
	results = 0
	search_results = search.search(query, qtype, page_num)
	
	if len(search_results) > 0:
		if isinstance(search_results[-1][0], int):
			results = search_results[-1][0]
		del search_results[-1]
	
	return render_template('results.html',
			query=query,
			results=results,
			search_results=search_results,
			qtype=qtype,
			pageNum=page_num)

@app.route("/", methods=["GET"])
def index():
	if request.method == "GET":
		pass
	return render_template('index.html')

if __name__ == "__main__":
	app.run(host='0.0.0.0')
