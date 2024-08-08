from html import unescape

from chompjs import parse_js_object
from scrapy import Spider

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS_DE, OpeningHours


class HitDESpider(Spider):
    name = "hit_de"
    item_attributes = {"brand": "HIT", "brand_wikidata": "Q1548713", "extras": Categories.SHOP_SUPERMARKET.value}
    allowed_domains = ["www.hit.de"]
    start_urls = ["https://www.hit.de/maerkte?ajax=1"]

    def parse(self, response):
        js_blob = unescape(response.xpath("//div/@data-stores").get())
        for location in parse_js_object(js_blob):
            item = DictParser.parse(location)
            item["ref"] = location["url"].split("/")[-1]
            item["street_address"] = item.pop("street")

            item["opening_hours"] = OpeningHours()
            for day_hours in location.get("openings", []):
                for day_of_week in day_hours["daysOfWeek"]:
                    item["opening_hours"].add_range(
                        DAYS_DE[day_of_week], day_hours["openedFrom"], day_hours["openedTo"]
                    )

            yield item
