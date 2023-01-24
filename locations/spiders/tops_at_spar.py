from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.spiders.vapestore_gb import clean_address


class TopsSpider(Spider):
    name = "tops"
    item_attributes = {"brand": "Tops", "brand_wikidata": "Q116377563"}
    skip_auto_cc = True

    def start_requests(self):
        yield JsonRequest(
            url="https://www.topsatspar.co.za/api/stores/search",
            data={"SearchText": "", "Types": ["TOPS"], "Services": []},
        )

    def parse(self, response, **kwargs):
        for location in response.json():
            location["location"] = {"lat": location["GPSLat"], "lon": location["GPSLong"]}
            location["street_address"] = location["PhysicalAddress"]
            location["address"] = clean_address([location["PhysicalAddress"], location["Suburb"], location["Town"]])
            location["Url"] = f'https://www.topsatspar.co.za/{location["Url"]}'

            yield DictParser.parse(location)
