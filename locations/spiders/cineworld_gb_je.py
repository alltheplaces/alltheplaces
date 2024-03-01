import json
import re

from scrapy import Spider

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class CineworldGBJESpider(Spider):
    name = "cineworld_gb_je"
    item_attributes = {"brand": "Cineworld", "brand_wikidata": "Q5120901"}
    start_urls = ["https://www.cineworld.co.uk/"]
    requires_proxy = "GB"

    def parse(self, response, **kwargs):
        for location in json.loads(re.search(r"apiSitesList = (\[.+\]),", response.text).group(1)):
            item = DictParser.parse(location)
            item["street_address"] = merge_address_lines(
                [
                    location["address"]["address1"],
                    location["address"]["address2"],
                    location["address"]["address3"],
                    location["address"]["address4"],
                ]
            )
            if item.get("postcode") and len(item["postcode"]) >= 2 and item["postcode"][:2] == "JE":
                item["country"] = "JE"
            else:
                item["country"] = "GB"
            item["ref"] = location["externalCode"]
            item["website"] = response.urljoin("{}/{}".format(location["uri"], location["externalCode"]))

            yield item
