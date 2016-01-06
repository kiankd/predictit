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

def extract_from_url(url):
	data = []

	page = urllib2.urlopen(url, 'html.parser')
	soup = BeautifulSoup(page.read(),"lxml")

	section_names = soup.find_all("h2", {"class":"inline-block"})
	section_names = [tag.contents[0] for tag in section_names]

	market_lists = soup.find_all("div", {"id":"marketList"})

	if len(section_names) != len(market_lists):
		raise HTMLParseError('Unequal number of section names vs marketLists!')

	for section, market_html in itertools.izip(section_names, market_lists):
		print 'Extracting from section: \"%s\"...'%(section)
		contracts = market_html.find_all("div", {"class":"col-xs-12 col-sm-6 col-md-4"})

		for con in contracts:
			link = con.find("div",{"class":LINK_CLASS_NAME}).a['href']

			q = con.find("h3", {"class":QUESTION_CLASS_NAME}).contents[0]
			
			best_answers = con.find_all("td",{"class":ANSWER_CLASS_NAME})
			top = best_answers[0].find('a').contents[0]
			bot = best_answers[1].find('a').contents[0]

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

def row_equal(r1, r2):
	# print r1[0:4]
	# print r2[0:4]
	# print r1[0:4] == r2[0:4]
	return r1[0:4] == r2[0:4]
	# return r1[0:4].all() == r2[0:4].all() # i.e. section,link,question,answer are ==

def stringed(matrix):
	ret = []
	for i in range(len(matrix)):
		s = ''
		for j in range(len(matrix[i])):
			s += matrix[i][j]
		ret.append(s)
	return ret

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

def add_new_data(new_data, file_name):
	print 'Adding new data parse to: %s...'%file_name

	old_data = []
	with open(file_name, 'rb') as csvfile:
		reader = csv.reader(csvfile, delimiter=',')
		for row in reader:
			old_data.append(row)

	str_old_data = stringed(np.array(old_data)[:,:len(HEADERS)])
	str_new_data = stringed(np.array(new_data)[:,:len(HEADERS)])

	old_header = old_data[0]
	empty_cols = len(old_header) - len(HEADERS) # Let's me know how many columns to skip for new/deleted entries.

	new_rows = [old_header+[get_time_string()]]

	old_i,new_i = 1,0 # skip header row (no header in new_data)
	print len(str_old_data),len(str_new_data)
	while old_i < len(str_old_data) or new_i < len(str_new_data):
		# print old_i,new_i
		if old_i < len(str_old_data) and new_i < len(str_new_data) and str_old_data[old_i] == str_new_data[new_i]:
			new_rows.append(old_data[old_i]+[new_data[new_i][-1]]) # Add the value is in last column.
			old_i += 1
			new_i += 1
		else:
			change = lambda x: x+1
			changed = False
			# If there is a new question/answer not present originally.
			if new_i < len(str_new_data) and str_new_data[new_i] not in str_old_data:
				new_rows.append(new_data[new_i][:-1] + ['' for _ in range(empty_cols)] + [new_data[new_i][-1]])
				new_i += 1
				changed = True
			else:
				orig = new_i
				while str_new_data[new_i] != str_old_data[old_i]:
					changed = True
					new_i = change(new_i)
					if new_i >= len(str_new_data):
						new_i = orig
						change = lambda x: x-1
					if new_i < 0:
						print 'ERROR: Infinite loop new_i!'
						exit(0)

			change = lambda x: x+1
			# If there is an old question/answer not present now.
			if old_i < len(str_old_data) and str_old_data[old_i] not in str_new_data:
				new_rows.append(rows[old_i] + ['' for _ in range(empty_cols)])
				old_i += 1
				changed = True
			elif not changed:
				orig = old_i
				while str_old_data[old_i] != str_new_data[new_i]:
					changed = True
					old_i = change(old_i)
					if old_i >= len(str_old_data):
						old_i = orig
						change = lambda x: x-1
					if old_i < 0:
						print 'ERROR: Infinite loop old_i!'
						exit(0)

	with open(file_name, 'wb') as csvfile:
		print 'Updating file: %s'%file_name
		writer = csv.writer(csvfile, delimiter=',')
		for newrow in new_rows:
			writer.writerow(newrow)
	print

# ----------------------------------------------------------------------- #
# Main...
if __name__ == '__main__':
	pages = {'elections':'https://www.predictit.org/Browse/Category/6/US-Elections',
			'politics':'https://www.predictit.org/Browse/Category/13/US-Politics',
			'world':'https://www.predictit.org/Browse/Category/4/World'}

	for name in pages:
		data = extract_from_url(pages[name])
		# first_save(data, DATA_FILES_LOCATION+name+'.csv')
		add_new_data(data, DATA_FILES_LOCATION+name+'.csv')


# ----------------------------------------------------------------------- #
