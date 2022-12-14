import os
from icrawler.builtin import GoogleImageCrawler, FlickrImageCrawler
import csv
import time
import flickrapi
from api_keys import FLICKR_KEY, FLICKR_SECRET
flickr = flickrapi.FlickrAPI(FLICKR_KEY, FLICKR_SECRET, format='parsed-json')
#resp = flickr.urls.lookupGroup(api_key = FLICKR_KEY, url = "https://www.flickr.com/groups/architecturelab/")
#print(resp)
streets_flickr_group = "1468642@N24"


#google_crawler = GoogleImageCrawler(
    #feeder_threads=1,
    #parser_threads=2,
    #downloader_threads=4,
    #storage={'root_dir': os.path.join(os.getcwd(), "images")})
#filters = dict(
    #type= "photo",
    #size='=1920x1080')
pools = {}
pools["silence"] = "1425976@N24"
pools["architecture"] = "1468642@N24"
pools["lonecity"] = "91283770@N00"
pools["pure_landscaped"] = "1191681@N23"
pools["empty_houses"] = "51594024@N00"
flickr_crawler = FlickrImageCrawler(FLICKR_KEY,
                            storage={'root_dir': os.path.join(os.getcwd(), "images4")})
flickr_crawler.crawl(max_num=1000, group_id=pools["empty_houses"], file_idx_offset=2000)
exit()

#with open(os.path.join(os.getcwd(), "datasets", "cities_list.csv")) as sources_file:
#initial_offset = 1222
#with open(os.path.join(os.getcwd(), "datasets", "coutries_list.csv")) as sources_file:
p1 = 100000
p2 = 250000
p3 = 500000
p4 = 1000000
p5 = 2500000
with open(os.path.join(os.getcwd(), "datasets", "world_cities_parsed.csv")) as sources_file:
    reader = csv.reader(sources_file)
    for i, line in enumerate(reader):
        print(line)
        #city, country = line
        city, country, population = line
        population = int(population)
        images_to_fetch = 1 if population < p1 else 2 if population < p2 else 3 if population < p3 else 4 if population < p4 else 5
        google_crawler.crawl(keyword=f'{city} {country}', filters=filters, offset=0, max_num=5, file_idx_offset=initial_offset)
        initial_offset += images_to_fetch
        #if i == 10:
            #break

# import flickrapi
# from api_keys import FLICKR_KEY, FLICKR_SECRET
# flickr = flickrapi.FlickrAPI(FLICKR_KEY, FLICKR_SECRET)
#
# lat = 48.83417
# lon = 12.221111
# photo_list = flickr.photos.search(api_key=FLICKR_KEY, lat=lat, lon=lon, accuracy=11, format='parsed-json')
# print(photo_list)
# first_photo = photo_list["photos"]["photo"][0]
# first_photo_id = first_photo["id"]
# shorturl = flickrapi.shorturl.url(first_photo_id)
#
