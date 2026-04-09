from typing import Any

from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class GameZASpider(Spider):
    name = "game_za"
    item_attributes = {"brand": "Game", "brand_wikidata": "Q126811048"}
    start_urls = ["https://www.game.co.za/occ/v2/game/stores?fields=FULL"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        sel = Selector(text=response.text, type="xml")
        for location in sel.xpath("//stores"):
            item = Feature()
            item["ref"] = location.xpath("./name/text()").get()
            item["branch"] = location.xpath("./displayName/text()").get().removeprefix("Game ")
            item["addr_full"] = location.xpath(".//address/formattedAddress/text()").get()
            item["state"] = location.xpath(".//address/region/name/text()").get()
            item["phone"] = location.xpath(".//address/phone/text()").get()
            item["email"] = location.xpath(".//address/email/text()").get()
            item["lat"] = location.xpath(".//geoPoint/latitude/text()").get()
            item["lon"] = location.xpath(".//geoPoint/longitude/text()").get()
            item["website"] = "https://www.game.co.za/"
            apply_category(Categories.SHOP_SUPERMARKET, item)
            item["opening_hours"] = self.parse_opening_hours(location)
            yield item

    def parse_opening_hours(self, location: Selector) -> OpeningHours:
        oh = OpeningHours()
        try:
            for day_time in location.xpath(".//openingHours//weekDayOpeningList"):
                day = day_time.xpath("./weekDay/text()").get()
                open_time = day_time.xpath("./openingTime/formattedHour/text()").get()
                close_time = day_time.xpath("./closingTime/formattedHour/text()").get()
                oh.add_range(day, open_time, close_time, "%I:%M %p")
        except Exception:
            pass
        return oh
