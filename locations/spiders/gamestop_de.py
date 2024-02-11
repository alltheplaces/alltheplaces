from scrapy import Selector

from locations.hours import DAYS_DE, OpeningHours
from locations.items import Feature
from locations.spiders.gamestop_ca import GamestopCASpider


class GamestopDESpider(GamestopCASpider):
    name = "gamestop_de"
    allowed_domains = ["www.gamestop.de"]
    start_urls = ["https://www.gamestop.de/StoreLocator/GetStoresForStoreLocatorByProduct"]

    @staticmethod
    def extract_hours(item: Feature, location: dict):
        if not location.get("Hours"):
            yield item
            return
        hours_string = " ".join(
            filter(None, map(str.strip, Selector(text=location["Hours"]).xpath("//td/text()").getall()))
        )
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string, days=DAYS_DE)
        yield item
