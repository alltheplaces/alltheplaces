from html import unescape
from urllib.parse import urljoin

from parsel import Selector

from locations.hours import DAYS_EN, OpeningHours
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class LaserawayUSSpider(WPStoreLocatorSpider):
    name = "laseraway_us"
    item_attributes = {
        "brand_wikidata": "Q119982751",
        "brand": "LaserAway",
    }
    allowed_domains = [
        "www.laseraway.com",
    ]
    days = DAYS_EN
    time_format = "%I:%M %p"

    def parse_item(self, item, location):
        del item["addr_full"]
        item["branch"] = unescape(item.pop("name").removeprefix("LaserAway ")).removeprefix("– ")
        item["website"] = urljoin("https://www.laseraway.com", location["url"])
        yield item

    def parse_opening_hours(self, location, days):
        if not location.get("hours"):
            return
        selector = Selector(text=location["hours"])
        if text := selector.xpath("//p/text()").get():
            oh = OpeningHours()
            oh.add_ranges_from_string(text, days=days)
            return oh
        else:
            return super().parse_opening_hours(location, days)
