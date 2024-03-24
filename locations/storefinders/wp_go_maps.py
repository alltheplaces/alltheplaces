import zlib
import json
from scrapy import Spider, Request

from locations.dict_parser import DictParser

# A base spider for WP Go Maps (https://wordpress.org/plugins/wp-google-maps/ and https://www.wpgmaps.com/)
#
# Supply `allowed_domains` or explicit `start_urls`
#
#https://www.wpgmaps.com/wp-json/wpgmza/v1/marker-listing/base64eJyrVirIKHDOSSwuVrJSCg9w941yjInxTSzKTi3yySwuycxLj4lxSizOTAbxlHSUiksSi0qUrAx0lHJS89JLMpSsDIHs3MSC+MwUINu0FgB6phsI
#  eJyrVirIKHDOSSwuVrJSCg9w941yjInxTSzKTi3yySwuycxLj4lxSizOTAbxlHSUiksSi0qUrAx0lHJS89JLMpSsDIHs3MSC+MwUINu0FgB6phsI Gzip decompresses to:
# {"phpClass":"WPGMZA\\MarkerListing\\BasicList","start":0,"length":10,"map_id":15}
#
class WpGoMapsSpider(Spider):
    map_id = None
    length = 10000
    start = 0

    start_urls = []
    allowed_domains = []

    # def start_requests(self):
    #     data = {
    #         "map_id": self.map_id,
    #         "length": self.length,
    #         "start": self.start
    #     }
    #     yield Request(url=self.start_urls[0], data=data, method="POST")


    def encode_params(self, params):
        return 'base64' + json.dumps(params).encode("zlib")

    def pre_process_marker(self, marker):
        if "<img" in marker["title"]:
            marker.pop("title")

        if "<img" in marker["address"]:
            marker.pop("address")
        return marker

    def parse_stores(self, response):
        for marker in response.json()["markers"]:
            yield DictParser.parse(self.pre_process_marker(marker))
