from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.user_agents import BROWSER_DEFAULT


class PaknsaveNZSpider(Spider):
    name = "paknsave_nz"
    start_urls = ["https://www.paknsave.co.nz/BrandsApi/BrandsStore/GetBrandStores"]
    item_attributes = {"brand": "PAK'nSAVE", "brand_wikidata": "Q7125339"}
    user_agent = BROWSER_DEFAULT

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["website"] = response.urljoin(location["url"])

            item["opening_hours"] = OpeningHours()
            for rule in location["openingHours"].split(";"):
                item["opening_hours"].add_range(*rule.replace(".", ":").split("-"), time_format="%I:%M%p")

            yield item
