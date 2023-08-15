import json
import re

from scrapy import Spider

from locations.dict_parser import DictParser
from locations.spiders.vapestore_gb import clean_address


class CineworldGBSpider(Spider):
    name = "cineworld_gb"
    item_attributes = {"brand": "Cineworld", "brand_wikidata": "Q5120901"}
    start_urls = ["https://www.cineworld.co.uk/"]
    requires_proxy = "GB"

    def parse(self, response, **kwargs):
        for location in json.loads(re.search(r"apiSitesList = (\[.+\]),", response.text).group(1)):
            item = DictParser.parse(location)
            item["street_address"] = clean_address(
                [
                    location["address"]["address1"],
                    location["address"]["address2"],
                    location["address"]["address3"],
                    location["address"]["address4"],
                ]
            )
            item["ref"] = location["externalCode"]
            item["website"] = response.urljoin("{}/{}".format(location["uri"], location["externalCode"]))

            yield item
