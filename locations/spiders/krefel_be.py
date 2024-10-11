import xmltodict
from scrapy import Spider

from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class KrefelBESpider(Spider):
    name = "krefel_be"
    item_attributes = {"brand": "Krëfel", "brand_wikidata": "Q3200093"}
    start_urls = ["https://api.krefel.be/api/v2/krefel/stores?pageSize=100&lang=nl"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response, **kwargs):
        # API response's content-type is not consistent.
        if response.headers["Content-Type"] == "application/json":
            locations = response.json()["stores"]
        else:
            locations = xmltodict.parse(response.text)["storeFinderSearchPage"]["stores"]
        for location in locations:
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
