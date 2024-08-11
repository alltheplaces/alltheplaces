import base64
import json
import zlib

from scrapy import Request, Spider

from locations.dict_parser import DictParser

# A base spider for WP Go Maps (https://wordpress.org/plugins/wp-google-maps/ and https://www.wpgmaps.com/)
#
# Supply `allowed_domains` or explicit `start_urls`.
# Optionally, filter to a specific map_id


class WpGoMapsSpider(Spider):
    map_id = None
    length = 10000
    start = 0

    start_urls = []
    allowed_domains = []

    def start_requests(self):
        urls = self.start_urls
        if len(self.start_urls) == 0:
            if self.map_id is not None:
                urls.append(self.features_url_for(self.map_id))
            else:
                urls.append(f"https://{self.allowed_domains[0]}/wp-json/wpgmza/v1/features/")

        for url in urls:
            yield Request(url=url, callback=self.parse)

    def parse(self, response, **kwargs):
        yield from self.parse_stores(response)

    def features_url_for(self, map_id):
        param = {"filter": json.dumps({"map_id": map_id})}
        return f"https://{self.allowed_domains[0]}/wp-json/wpgmza/v1/features/{self.encode_params(param)}"

    # https://www.wpgmaps.com/wp-json/wpgmza/v1/marker-listing/base64eJyrVirIKHDOSSwuVrJSCg9w941yjInxTSzKTi3yySwuycxLj4lxSizOTAbxlHSUiksSi0qUrAx0lHJS89JLMpSsDIHs3MSC+MwUINu0FgB6phsI
    #  eJyrVirIKHDOSSwuVrJSCg9w941yjInxTSzKTi3yySwuycxLj4lxSizOTAbxlHSUiksSi0qUrAx0lHJS89JLMpSsDIHs3MSC+MwUINu0FgB6phsI Gzip decompresses to:
    # {"phpClass":"WPGMZA\\MarkerListing\\BasicList","start":0,"length":10,"map_id":15}
    def encode_params(self, params):
        data = zlib.compress(json.dumps(params).encode())
        path = base64.b64encode(data).rstrip(b"=").decode()
        return f"base64{path}"

    def pre_process_marker(self, marker):
        if "<img" in marker["title"]:
            marker.pop("title")

        if "<img" in marker["address"]:
            marker.pop("address")
        return marker

    def post_process_item(self, item, location):
        return item

    def parse_stores(self, response):
        for marker in response.json()["markers"]:
            location = self.pre_process_marker(marker)
            item = DictParser.parse(location)
            yield self.post_process_item(item, location)
