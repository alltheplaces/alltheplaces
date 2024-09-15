import base64
import json
import zlib
from typing import Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.items import Feature

# A base spider for WP Go Maps (https://wordpress.org/plugins/wp-google-maps/
# and https://www.wpgmaps.com/).
#
# Supply `allowed_domains` as the domain containing the store finder page.
# In some rare circumstances where the WordPress API endpoint is in a custom
# path, specify an explicit `start_urls` to the path of
# `/wp-json/wpgmza/v1/features/`.
#
# This store finder allows multiple feature layers to be returned from the
# same API endpoint. Most store locator implementations will only have a
# single feature layer with identifier of "1". Only in circumstances where
# a different feature layer needs to be used should a value for the `map_id`
# attribute of this class be supplied. All valid `map_id` values can be found
# by typing `window.WPGMZA.maps.map(i => {return i.id})` into a Firefox
# JavaScript console on the store finder page to observe any identifiers
# returned other than the default of "1".
#
# If clean-up to extracted data is required, or additional data fields need to
# be extracted, override the `post_process_item` method.


class WpGoMapsSpider(Spider):
    map_id: int = None
    length: int = 10000
    start: int = 0

    start_urls = []
    allowed_domains = []

    def start_requests(self) -> Iterable[Request]:
        urls = self.start_urls
        if len(self.start_urls) == 0:
            if self.map_id is not None:
                urls.append(self.features_url_for(self.map_id))
            else:
                urls.append(f"https://{self.allowed_domains[0]}/wp-json/wpgmza/v1/features/")

        for url in urls:
            yield Request(url=url, callback=self.parse)

    def parse(self, response: Response) -> Iterable[Feature]:
        yield from self.parse_stores(response)

    def features_url_for(self, map_id: int) -> str:
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

    def post_process_item(self, item: Feature, location: dict) -> Feature:
        return item

    def parse_stores(self, response: Response) -> Iterable[Feature]:
        for marker in response.json()["markers"]:
            self.pre_process_data(marker)
            location = self.pre_process_marker(marker)
            item = DictParser.parse(location)
            yield self.post_process_item(item, location)

    def pre_process_data(self, location, **kwargs):
        """Override with any pre-processing on the item."""
