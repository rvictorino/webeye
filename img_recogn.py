from clarifai import rest
from clarifai.rest import ClarifaiApp
import argparse
from urlparse import urlparse
import urllib2
import urllib
import json

import cam_discovery

MAPS_API_KEY = ""
OUTPUT_FILE_PATH = "/var/www/html/webeye/webeye.js"

def get_url_list_from_file(file_path):
	file_to_read=open(file_path,'r')
	return file_to_read.readlines()


def get_location(uri):
	domain = urlparse(uri).netloc.split(":")[0]
	result = urllib2.urlopen("http://ip-api.com/json/" + str(domain)).read()
	parsed = json.loads(result)
	return {"lat": parsed["lat"], "lon": parsed["lon"]}


def generate_map(located_images_list):
	url_base = "https://maps.googleapis.com/maps/api/staticmap?"
	params = {"key": MAPS_API_KEY, "size": "500x400"}
	
	# generate markers
	markers = []
	for located_img in located_images_list:
		loc = located_img["location"]
		markers.append("markers=color:blue%7Clabel:M%7C{0},{1}".format(loc["lat"], loc["lon"]))
	final_url = url_base + urllib.urlencode(params) + "&" + "&".join(markers)
	return final_url


def generate_JSON_file(located_images_list):
	dest_file = open(OUTPUT_FILE_PATH, 'w')
	json_data = json.dumps(located_images_list)
	print >> dest_file, "var webeye = " + json_data
	dest_file.close()


def remove_port_from_url(url):
	parsed_url = urlparse(url)
	if parsed_url.port == 80:
		return parsed_url.scheme + "://" + parsed_url.netloc[:-3] + parsed_url.path
	return parsed_url.geturl()

parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-u", help="url to the image to predict")
group.add_argument("-f", help="path to file containing list of image urls")
group.add_argument("-n", type=int, default=6, help="number of url to import")
parser.add_argument("--static", action='store_true', help="output a google static map url")
args = parser.parse_args()

# parse arguments: one url or a list within a file ?
if args.u is not None:
	url_list = [args.u]
elif args.f is not None:
	url_list = get_url_list_from_file(args.f)
else:
	url_list = cam_discovery.get_best_cam_urls(args.n)


# init ClarifAi app
print("Connecting to ClarifAi")
app = ClarifaiApp("", "")
model = app.models.get("general-v1.3")

geo_data = []

# parse each url
for img_url in url_list:

	geo_concept = {}
	img_url = remove_port_from_url(img_url)
	print(img_url)

	# get image url
	geo_concept["url"] = img_url

	# get lat / lon from IP or domain
	geo_concept["location"] = get_location(img_url)

	# get concepts in image
	geo_concept["concepts"] = []
	result = model.predict_by_url(url=img_url)
	for concept in result["outputs"][0]["data"]["concepts"]:
		print("{0:s}: {1:.2f}%".format(concept["name"], concept["value"]*100))
		geo_concept["concepts"].append({"concept": str(concept["name"]), "probability": concept["value"]*100})

	# feed the list
	geo_data.append(geo_concept)


#TODO: use these data to generate a dynamic google map, including concepts data as tooltips
if args.static:
	map_url = generate_map(geo_data)
	print(map_url)
else:
	# dynamic map
	generate_JSON_file(geo_data)

