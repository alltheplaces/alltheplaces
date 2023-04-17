import json

from scrapy import Spider

from locations.dict_parser import DictParser


class EvyveGBSpider(Spider):
    name = "evyve_gb"
    item_attributes = {"brand": "evyve", "brand_wikidata": "Q116698197"}
    start_urls = ["https://evyve.co.uk/locations/"]

    def parse(self, response):
        locations = json.loads(
            response.xpath('//main[@id="content"]/script')
            .get()
            .split("var propertyLocations = JSON.parse('", 2)[1]
            .split("');", 2)[0]
        )
        for location in locations:
            print(location)
            if not location["publish"]:
                continue  # location not open (coming soon or other reason)
            item = DictParser.parse(location)
            # Address fields are all jumbled up it's best to combine them together
            item["addr_full"] = ", ".join(
                filter(None, [location["address"], location["address_line_2"], location["city"]])
            )
            item.pop("city")
            item["extras"]["access"] = location["access_type"].lower()
            yield item
