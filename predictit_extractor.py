"""
Author: Kian Kenyon-Dean

Note that time signatures are structured as follows:
	YEAR-MONTH-DAY-MINUTE-HOUR
	YYYY-MM-DD-hh-mm

Data organization:
	'section','link','question','answer', vals...
"""

from os import listdir
from bs4 import BeautifulSoup
import numpy as np
import datetime
import urllib2
import itertools
import time
import csv
import pandas
import sys

# ----------------------------------------------------------------------- #
# Global Variables...

TAG_DATE = "20150803" # Not sure if this will change or not in the future.

LINK_CLASS_NAME = "_"+TAG_DATE+"_browse"
QUESTION_CLASS_NAME = "_"+TAG_DATE+"_question"
ANSWER_CLASS_NAME = "_"+TAG_DATE+"_h-class-1 _"+TAG_DATE+"_border"
VALUE_CLASS_NAME = "_"+TAG_DATE+"_h-class-2r _"+TAG_DATE+"_border"

DATA_FILES_LOCATION = 'data_files/'

HEADERS = {0:'section', 1:'link', 2:'question', 3:'answer'}

# ----------------------------------------------------------------------- #
# Custom Classes and helpers...
class HTMLParseError(Exception): 
	pass

def ascii(text):
	''' Returns the string without non ASCII characters'''
	stripped = (c for c in text if 0 < ord(c) < 127)
	return ''.join(stripped)

def extract_from_url(url):
	data = []

	page = urllib2.urlopen(url, 'html.parser')
	soup = BeautifulSoup(page.read(),"lxml")

	section_names = soup.find_all("h2", {"class":"inline-block"})
	section_names = [ascii(tag.contents[0]) for tag in section_names]

	market_lists = soup.find_all("div", {"id":"marketList"})

	if len(section_names) != len(market_lists):
		raise HTMLParseError('Unequal number of section names vs marketLists!')

	for section, market_html in itertools.izip(section_names, market_lists):
		# print 'Extracting from section: \"%s\"...'%(section)
		contracts = market_html.find_all("div", {"class":"col-xs-12 col-sm-6 col-md-4"})

		for con in contracts:
			link = con.find("div",{"class":LINK_CLASS_NAME}).a['href']

			q = ascii(con.find("h3", {"class":QUESTION_CLASS_NAME}).contents[0])
			
			best_answers = con.find_all("td",{"class":ANSWER_CLASS_NAME})
			top = ascii(best_answers[0].find('a').contents[0])
			bot = ascii(best_answers[1].find('a').contents[0])

			best_values = con.find_all("td",{"class":VALUE_CLASS_NAME})
			
			# This try/except is done because there are slightly different <span> attributes
			# for yes/no vs. the multi-answer ones.
			try: 
				top_val = int(best_values[0].find('span').contents[0]) 		
				bot_val = int(best_values[1].find('span').contents[0])
			except ValueError:
				try:
					top_val = int(best_values[0].contents[0])
					bot_val = int(best_values[1].contents[0])
				except ValueError:
					raise HTMLParseError('Bad parse when extracting share values!')

			data.append([section, link, q, top, top_val])
			data.append([section, link, q, bot, bot_val])

	return data

def get_time_string():
	now = datetime.datetime.now()
	return '%s-%s-%s-%s-%s'%(now.year,now.month,now.day,now.hour,now.minute)

SPLITTER = ':::'

def stringed_list(lst):
	s = ''
	for item in lst:
		s += item+SPLITTER
	return s[:-len(SPLITTER)]

def listed_string(string):
	return string.split(SPLITTER)

# ----------------------------------------------------------------------- #
# Data saving...

def first_save(data, file_name):
	print 'Writing new file: %s...'%file_name
	with open(file_name, 'wb') as csvfile:
		writer = csv.writer(csvfile, delimiter=',')
		writer.writerow(['section','link','question','answer',get_time_string()])
		for row in data:
			writer.writerow(row)
	print

def add_new_data2(data, file_name, verbose=True):
	if verbose:
		print 'Adding new data parse to: %s...'%file_name

	old_data = {}
	old_header = []
	with open(file_name, 'rb') as csvfile:
		reader = csv.reader(csvfile, delimiter=',')
		for row in reader:
			if not old_header:
				old_header = row
			else:
				old_data[stringed_list(row[:len(HEADERS)])] = row[len(HEADERS):]

	new_data = {}
	for row in data:
		new_data[stringed_list(row[:len(HEADERS)])] = row[len(HEADERS):]

	# Let's me know how many columns to skip for new/deleted entries.
	num_empty_cols = len(old_header) - len(HEADERS) 
	empty_col_list = ['' for _ in range(num_empty_cols)]

	new_rows = [old_header+[get_time_string()]]

	for key in sorted(old_data):
		try:
			newrow = listed_string(key) + old_data[key] + new_data[key]
			new_rows.append(newrow)
		except KeyError:
			# Then this is an old question that has been resolved.
			newrow = listed_string(key) + old_data[key] + empty_col_list
			new_rows.append(newrow)

	for key in sorted(new_data):
		try:
			old_data[key]
			pass
		except KeyError:
			# We have a new question that wasn't present in the previous extraction.
			newrow = listed_string(key) + empty_col_list + [new_data[key]]
			new_rows.append(newrow)

	with open(file_name, 'wb') as csvfile:
		if verbose:
			print 'Updating file: %s\n'%file_name
		writer = csv.writer(csvfile, delimiter=',')
		for newrow in new_rows:
			writer.writerow(newrow)

# ----------------------------------------------------------------------- #
# Main...
if __name__ == '__main__':
	pages = {'elections':'https://www.predictit.org/Browse/Category/6/US-Elections',
			'politics':'https://www.predictit.org/Browse/Category/13/US-Politics',
			'world':'https://www.predictit.org/Browse/Category/4/World'}

	for name in pages:
		data = extract_from_url(pages[name])

		if len(sys.argv) != 3:
			print 'Please call with 2 arguments:'
 			print '    $ python predictit_extractor.py NEW/UPDATE NAME_OF_NEW_FILES'
			exit(0)

		filename = name+sys.argv[2]+'.csv'

		if sys.argv[1] == 'new':
			first_save(data, DATA_FILES_LOCATION+filename)
		
		elif sys.argv[1] == 'update':
			filename = name+sys.argv[2]+'.csv'
			
			if not filename in listdir(DATA_FILES_LOCATION):
				print 'File %s not found! Try calling this with the "new" arg first!'
				exit(0)

			if name == 'elections':
				print 'Updating %s...'%(get_time_string())
			add_new_data2(data, DATA_FILES_LOCATION+filename, verbose=False)


# ----------------------------------------------------------------------- #
