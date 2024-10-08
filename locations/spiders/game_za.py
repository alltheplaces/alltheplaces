from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class GameZASpider(Spider):
    name = "game_za"
    item_attributes = {"brand": "Game", "brand_wikidata": "Q129263113"}
    start_urls = ["https://api-beta-game.walmart.com/occ/v2/game/stores?fields=FULL"]
    requires_proxy = True

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["stores"]:
            item = DictParser.parse(location)
            item["ref"] = item.pop("name")
            item["branch"] = location["displayName"].replace(self.item_attributes["brand"], "").strip()
            item["street_address"] = location["address"].get("streetAddress")
            item["city"] = location["address"].get("town")
            try:
                item["state"] = location["address"].get("region").get("name")
            except:
                pass
            item["postcode"] = location["address"].get("postalCode")
            item["phone"] = location["address"].get("phone")
            item["email"] = location["address"].get("email")

            # Url is given, but redirects to homepage
            item.pop("website")
            # item["website"] = "https://www.game.co.za" + location["url"]

            if "openingHours" in location:
                item["opening_hours"] = OpeningHours()
                for day in location["openingHours"]["weekDayOpeningList"]:
                    if day["closed"]:
                        item["opening_hours"].set_closed(day["weekDay"])
                    else:
                        item["opening_hours"].add_range(
                            day["weekDay"],
                            day["openingTime"]["formattedHour"].upper(),
                            day["closingTime"]["formattedHour"].upper(),
                            "%I:%M %p",
                        )
            yield item
