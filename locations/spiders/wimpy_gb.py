import scrapy

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class WimpyGBSpider(scrapy.Spider):
    name = "wimpy_gb"
    item_attributes = {"brand": "Wimpy", "brand_wikidata": "Q2811992"}
    start_urls = ["https://wimpy.uk.com/api/v2/locations?all=true"]

    def parse(self, response, **kwargs):
        for location in response.json()["locations"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name").removeprefix("Wimpy ")
            item.pop("addr_full", None)
            item["street_address"] = merge_address_lines([location["address_line_1"], location["address_line_2"]])
            yield item
