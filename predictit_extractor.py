from os import listdir
from bs4 import BeautifulSoup
import urllib2
import itertools
import time
import csv

# ----------------------------------------------------------------------- #
# Custom Classes...

class HTMLParseError(Exception): 
	pass

class Contract:
	def __init__(self,link,q,top,top_val,bot,bot_val):
		self.link = link
		self.q = q
		self.top = top
		self.top_val = top_val
		self.bot = bot
		self.bot_val = bot_val
		self.yes_no = top=='Yes' and bot=='No'
	
	def get_link(self):
		return "https://www.predictit.org"+self.link

# ----------------------------------------------------------------------- #
# Global Variables...

TAG_DATE = "20150803" # Not sure if this will change or not in the future.

LINK_CLASS_NAME = "_"+TAG_DATE+"_browse"
QUESTION_CLASS_NAME = "_"+TAG_DATE+"_question"
ANSWER_CLASS_NAME = "_"+TAG_DATE+"_h-class-1 _"+TAG_DATE+"_border"
VALUE_CLASS_NAME = "_"+TAG_DATE+"_h-class-2r _"+TAG_DATE+"_border"

DATA_FILES_LOCATION = './data_files/'

# ----------------------------------------------------------------------- #
# Extraction...

def extract_from_page(url):
	page = urllib2.urlopen(url, 'html.parser')
	soup = BeautifulSoup(page.read(),"lxml")

	section_names = soup.find_all("h2", {"class":"inline-block"})
	section_names = [tag.contents[0] for tag in section_names]

	market_lists = soup.find_all("div", {"id":"marketList"})

	if len(section_names) != len(market_lists):
		raise HTMLParseError('Unequal number of section names vs marketLists!')


	data_dict = {section:[] for section in section_names}
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

			data_dict[section].append(Contract(link,q,top,top_val,bot,bot_val))
	
	return data_dict

# ----------------------------------------------------------------------- #
# Saving...

def first_save(data, link, file_name):
	with open(file_name, 'wb') as csvfile:
		mywriter = csv.writer(csvfile, delimiter=',')
		mywriter.writerow(['section','link','question','answer','answer_value'])
		

	return

# ----------------------------------------------------------------------- #
# Main...
if __name__ == '__main__':
	pages = {'elections':'https://www.predictit.org/Browse/Category/6/US-Elections',
			'politics':'https://www.predictit.org/Browse/Category/13/US-Politics',
			'world':'https://www.predictit.org/Browse/Category/4/World'}

	for key in pages:
		data = extract_from_page(pages[key])
		first_save(data, pages[key], key+'.csv')


# ----------------------------------------------------------------------- #



