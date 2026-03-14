from http.cookies import SimpleCookie

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class MadisonReedUSSpider(Spider):
    name = "madison_reed_us"
    item_attributes = {
        "brand": "Madison Reed",
        "brand_wikidata": "Q60770929",
    }

    # Need to get a token before making any API requests
    start_urls = ["https://www.madison-reed.com/store-locator"]

    def parse(self, response):
        # Parse token from response headers
        cookie = SimpleCookie()
        for line in response.headers.getlist("Set-Cookie"):
            cookie.load(line.decode())
        yield JsonRequest(
            "https://www.madison-reed.com/api/colorbar/getActiveWholesalesLocationsList",
            data={"lat": 0, "lon": 0, "maxDistance": 24901},
            headers={"x-csrf-stp": cookie["csrf_stp"].value},
            callback=self.parse_locations,
        )

    def parse_locations(self, response):
        for location in response.json():
            if location["type"] != "MR":
                continue
            item = DictParser.parse(location)
            item["branch"] = item.pop("name").removesuffix(" Hair Color Bar")
            item["street_address"] = merge_address_lines([location["address1"], location["address2"]])
            item["ref"] = location["code"]
            yield item
