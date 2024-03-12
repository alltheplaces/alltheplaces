import re

import chompjs
from scrapy import Request, Spider

from locations.items import Feature


class MtexxBGSpider(Spider):
    name = "mtexx_bg"
    item_attributes = {"brand": "M-texx", "brand_wikidata": "Q122947768"}
    allowed_domains = ["m-texx.com"]
    start_urls = ["https://m-texx.com/locations"]
    no_refs = True

    def parse(self, response, **kwargs):
        url = re.search(r"(static/chunks/app/\(website\)/locations/page-\w+\.js)", response.text)
        yield Request("https://m-texx.com/_next/" + url.group(1), callback=self.parse_locations)

    def parse_locations(self, response, **kwargs):
        locations = chompjs.parse_js_objects(re.search(r"exports=\[({city:.+}])}", response.text).group(1))
        for location in locations:
            properties = {
                "city": location["city"],
                "addr_full": location["popUp"],
                "lat": location["geocode"][0],
                "lon": location["geocode"][1],
            }
            yield Feature(**properties)
