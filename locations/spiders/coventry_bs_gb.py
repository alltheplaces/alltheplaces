
from scrapy import Spider

from locations.dict_parser import DictParser


class CoventryBSGBSpider(Spider):
    name = "coventry_bs_gb"
    item_attributes = {
        "brand": "Coventry Building Society",
        "brand_wikidata": "Q5179055",
    }
    start_urls = ["https://www.coventrybuildingsociety.co.uk/content/datasource/api/branch/allbranches.data.json"]

    def parse(self, response, **kwargs):
        for location in response.json()["branches"]:
            item = DictParser.parse(location)
            yield item
