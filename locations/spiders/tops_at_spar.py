from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class TopsAtSparSpider(Spider):
    name = "tops_at_spar"
    item_attributes = {"brand": "Tops", "brand_wikidata": "Q116377563"}
    skip_auto_cc_spider_name = True
    skip_auto_cc_domain = True

    def start_requests(self):
        yield JsonRequest(
            url="https://www.topsatspar.co.za/api/stores/search",
            data={"SearchText": "", "Types": ["TOPS"], "Services": []},
        )

    def parse(self, response, **kwargs):
        for location in response.json():
            location["location"] = {"lat": location["GPSLat"], "lon": location["GPSLong"]}
            location["street_address"] = location["PhysicalAddress"]
            location["address"] = merge_address_lines(
                [location["PhysicalAddress"], location["Suburb"], location["Town"]]
            )
            location["Url"] = f'https://www.topsatspar.co.za/{location["Url"]}'

            yield DictParser.parse(location)
