import re

from scrapy import Spider
from scrapy.http import Request

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class LifeTimeSpider(Spider):
    name = "life_time"
    item_attributes = {"brand": "Life Time", "brand_wikidata": "Q6545004"}
    allowed_domains = ["www.lifetime.life", "my.lifetime.life"]
    start_urls = ["https://www.lifetime.life/bin/lt/nearestClubServlet.locator.json?limit=10000&distance=15000"]
    custom_settings = {"ROBOTSTXT_OBEY": False}  # robots.txt is a HTML error page

    def parse(self, response):
        for location in response.json():
            if not location.get("clubId") or not location.get("open") or location["open"] != "open":
                # Only open stores appear to have a clubId defined
                continue
            item = DictParser.parse(location)
            item["ref"] = location["clubId"]
            item["website"] = location.get("clubPagePath")
            item["street_address"] = clean_address([location.get("street1"), location.get("street2")])
            if location.get("clubPagePaths") and location["clubPagePaths"].get("clubHours"):
                hours_url = location["clubPagePaths"]["clubHours"]
                yield Request(url=hours_url, callback=self.add_hours, meta={"item": item})
            else:
                yield item

    def add_hours(self, response):
        item = response.meta["item"]
        hours_text = re.sub(
            r"\s+",
            " ",
            " ".join(
                response.xpath('(//table[contains(@summary, "open hours summary")])[1]//td/text()').getall()
            ).strip(),
        )
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_text)
        yield item
