import urllib2
import re
from urlparse import urlparse
from HTMLParser import HTMLParser

# parse unsecure cam urls from insecam.org
# no other way to do this ?

# Fake user agent to avoid 403
HEADERS = {'User-Agent' : 'Magic Browser'}
BASE_URL = "https://www.insecam.org"

NEWEST_PAGE = "/en/bynew/"
MOST_P_PAGE = "/en/byrating/"

NUMBER_PER_PAGE = 6
PAGINATION_PARAM = "?page="

# define our own html insecam parser
class CamUrlParser(HTMLParser):

	cam_urls = []

	def handle_starttag(self, tag, attrs):
		attrs = dict(attrs)
		if self.is_cam_img(tag, attrs):
			self.cam_urls.append(self.parse_url(attrs["src"]))

	def is_cam_img(self, tag, attrs):
		if tag != 'img':
			return False
		if not "class" in attrs or "thumbnail-item__img" not in attrs["class"]:
			return False
		return True

	# specific url parsing
	def parse_url(self, url):
		if "/mjpg/video.mjpg" in url:
			url = re.sub("/mjpg/video.mjpg", "/jpg/image.jpg", url)
		return url		


# get x newest cam from insecam
def get_newest_cam_urls(n):
	return get_cam_urls(n, NEWEST_PAGE)

# get x best cam from insecam
def get_best_cam_urls(n):
	return get_cam_urls(n, MOST_P_PAGE)

# get x cam urls from insecam
def get_cam_urls(n, which):
	
	html_parser = CamUrlParser()
	
	page = 1
	while len(html_parser.cam_urls) < n:
		
		http_request = urllib2.Request(url=BASE_URL + which + PAGINATION_PARAM + str(page), headers=HEADERS)
		html_content = urllib2.urlopen(http_request).read()

		html_parser.feed(html_content)
		page += 1
	
	return html_parser.cam_urls

