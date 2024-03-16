from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class CrownDecoratingCentresGBSpider(Spider):
    name = "crown_decorating_centres_gb"
    item_attributes = {
        "brand": "Crown Decorating Centres",
        "brand_wikidata": "Q122839963",
        "extras": Categories.SHOP_PAINT.value,
    }
    allowed_domains = ["www.crowndecoratingcentres.co.uk"]
    start_urls = ["https://www.crowndecoratingcentres.co.uk/api/sitecore/crowndecorating/stores/search"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url)

    def parse(self, response):
        for location in response.json()["Stockists"]:
            item = DictParser.parse(location)
            item["ref"] = location["StoreCode"]
            item.pop("name", None)
            item["addr_full"] = ", ".join(
                filter(None, map(str.strip, [location.get("Address1"), location.get("Address2")]))
            )
            item["website"] = "https://www.crowndecoratingcentres.co.uk" + location["Url"]
            hours_string = ""
            for day_hours in location["StockistBusinessHours"]:
                if day_hours["OpenTime"] == day_hours["CloseTime"]:
                    continue
                hours_string = "{} {}: {} - {}".format(
                    hours_string, day_hours["DayOfWeek"], day_hours["OpenTime"], day_hours["CloseTime"]
                )
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)
            yield item
