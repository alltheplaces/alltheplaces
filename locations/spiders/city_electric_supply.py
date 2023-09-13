import json
import re

from scrapy import Spider

from locations.dict_parser import DictParser


class CityElectricSupplySpider(Spider):
    name = "city_electric_supply"
    item_attributes = {"brand": "City Electric Supply", "brand_wikidata": "Q121357206"}
    start_urls = ["https://www.cityelectricsupply.com/branchlocator", "https://www.cityelectricsupply.ca/branchlocator"]

    def parse(self, response, **kwargs):
        if data := re.search(r"var jsonAllBranches = (\[.+\]);", response.text):
            for location in json.loads(data.group(1)):
                item = DictParser.parse(location)
                item["extras"]["addr:unit"] = location["Address2"]
                item["name"] = location["BranchName"]
                item["ref"] = location["BranchId"]
                item["website"] = response.urljoin(f'/branch/{location["BranchId"]}')
                # TODO: root domain? location["MapImageUrl"]

                yield item
