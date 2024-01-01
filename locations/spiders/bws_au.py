from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class BWSAUSpider(Spider):
    name = "bws_au"
    item_attributes = {"brand": "BWS", "brand_wikidata": "Q4836848"}
    allowed_domains = ["store.bws.com.au"]
    start_urls = ["https://store.bws.com.au/locations.json"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        for location in response.json()["response"]["entities"]:
            item = DictParser.parse(location["profile"])
            item["ref"] = location["profile"]["meta"]["id"]
            item["lat"] = location["profile"]["yextDisplayCoordinate"]["lat"]
            item["lon"] = location["profile"]["yextDisplayCoordinate"]["long"]
            item["street_address"] = ", ".join(
                filter(
                    None,
                    [
                        location["profile"]["address"]["line1"],
                        location["profile"]["address"]["line2"],
                        location["profile"]["address"]["line3"],
                    ],
                )
            )
            item["website"] = "https://store.bws.com.au/" + location["url"]
            if location["profile"].get("mainPhone"):
                item["phone"] = location["profile"]["mainPhone"]["number"]
            if location["profile"].get("hours"):
                item["opening_hours"] = OpeningHours()
                for day_hours in location["profile"]["hours"]["normalHours"]:
                    for interval in day_hours["intervals"]:
                        item["opening_hours"].add_range(
                            day_hours["day"].title(), str(interval["start"]), str(interval["end"]), "%H%M"
                        )
            yield item
