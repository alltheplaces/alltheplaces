from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class IpItSmSpider(Spider):
    name = "ip_it_sm"
    item_attributes = {"brand": "IP", "brand_wikidata": "Q3788748"}
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    async def start(self):
        yield JsonRequest(
            url="https://www.italianapetroli.it/ricerca-stazioni-servizio/api/search",
            method="POST",
            callback=self.parse,
        )

    def parse(self, response: Response):
        for location in response.json():
            item = DictParser.parse(location)
            item["ref"] = location.get("stationCode")
            item["branch"] = location.get("label").removeprefix("Stazione di servizio ")
            item["street_address"] = item.pop("addr_full")
            item["state"] = location.get("district")
            apply_category(Categories.FUEL_STATION, item)
            yield item
