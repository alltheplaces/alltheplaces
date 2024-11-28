from scrapy import Spider

from locations.hours import OpeningHours
from locations.items import Feature


class GameZASpider(Spider):
    name = "game_za"
    item_attributes = {"brand": "Game", "brand_wikidata": "Q129263113"}
    start_urls = ["https://www.game.co.za/occ/v2/game/stores?fields=FULL"]

    def parse(self, response):
        for location in response.xpath("//stores"):
            item = Feature()
            item["name"] = location.xpath(".//displayName/text()").get()
            item["street_address"] = location.xpath(".//address//streetAddress/text()").get()
            item["city"] = location.xpath(".//town/text()").get()
            item["postcode"] = location.xpath(".//postalCode/text()").get()
            item["phone"] = location.xpath(".//phone/text()").get()
            item["addr_full"] = location.xpath(".//formattedAddress/text()").get()
            item["email"] = location.xpath(".//email/text()").get()
            item["lat"] = location.xpath(".//geoPoint/latitude/text()").get()
            item["lon"] = location.xpath(".//geoPoint/longitude/text()").get()
            item["ref"] = location.xpath(".//id/text()").get()
            item["website"] = "https://www.game.co.za/"
            item["opening_hours"] = OpeningHours()
            for day_time in location.xpath(".//openingHours//weekDayOpeningList"):
                day = day_time.xpath(".//weekDay/text()").get()
                open_time = day_time.xpath(".//openingTime/formattedHour/text()").get()
                close_time = day_time.xpath(".//closingTime/formattedHour/text()").get()
                item["opening_hours"].add_range(
                    day=day, open_time=open_time, close_time=close_time, time_format="%I:%M %p"
                )
            yield item
