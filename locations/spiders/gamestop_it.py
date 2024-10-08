from scrapy import Selector

from locations.hours import DAYS_IT, OpeningHours
from locations.items import Feature
from locations.spiders.gamestop_ca import GamestopCASpider


class GamestopITSpider(GamestopCASpider):
    name = "gamestop_it"
    allowed_domains = ["www.gamestop.it"]
    start_urls = ["https://www.gamestop.it/StoreLocator/GetStoresForStoreLocatorByProduct"]

    @staticmethod
    def extract_hours(item: Feature, location: dict):
        if not location.get("Hours"):
            yield item
            return
        hours_string = " ".join(
            filter(None, map(str.strip, Selector(text=location["Hours"]).xpath("//td//text()").getall()))
        ).replace(",", ":")
        hours_string = hours_string.replace("Chiuso", "")  # "Lunedi Chiuso 15:30 - 19:30" -> "Lunedi  15:30 - 19:30"
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string, days=DAYS_IT)
        item.pop("name", None)
        yield item
