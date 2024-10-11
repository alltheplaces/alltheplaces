from typing import Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class KrefelBESpider(Spider):
    name = "krefel_be"
    item_attributes = {"brand": "Krëfel", "brand_wikidata": "Q3200093"}
    user_agent = BROWSER_DEFAULT

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(url="https://api.krefel.be/api/v2/krefel/stores?pageSize=100&lang=nl")

    def parse(self, response, **kwargs):
        for location in response.json()["stores"]:
            location["ref"] = location.pop("name")
            location["website"] = f'https://www.krefel.be/nl/winkels/{location["ref"]}'
            location["phone"] = "; ".join(
                filter(None, [location["address"].get("phone"), location["address"].get("phone2")])
            ).replace("/", "")
            location["address"]["house_number"] = location["address"].pop("line2", "")
            location["address"]["street"] = location["address"].pop("line1")

            item = DictParser.parse(location)
            item["extras"]["website:fr"] = f'https://www.krefel.be/fr/magasins/{location["ref"]}'
            item["branch"] = item.pop("name")
            yield item
