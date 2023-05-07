from scrapy import Selector, Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours, sanitise_day
from locations.items import Feature
from locations.spiders.vapestore_gb import clean_address


# https://github.com/wp-plugins/wp-store-locator/blob/master/frontend/wpsl-ajax-functions.php#L15
class WPStoreLocatorSpider(Spider):
    days = DAYS_EN
    time_format = "%H:%S"

    def start_requests(self):
        if len(self.start_urls) == 0 and hasattr(self, "allowed_domains"):
            for domain in self.allowed_domains:
                yield JsonRequest(url=f"https://{domain}/wp-admin/admin-ajax.php?action=store_search&autoload=1")
        elif len(self.start_urls) != 0:
            for url in self.start_urls:
                yield JsonRequest(url=url)

    def parse(self, response, **kwargs):
        for location in response.json():
            location["street_address"] = clean_address([location.pop("address"), location.pop("address2")])
            item = DictParser.parse(location)
            item["name"] = location["store"]
            item["opening_hours"] = self.parse_opening_hours(location)
            yield from self.parse_item(item, location) or []

    def parse_item(self, item: Feature, location: dict, **kwargs):
        yield item

    def parse_opening_hours(self, location: dict, **kwargs) -> OpeningHours:
        if not location.get("hours"):
            return
        sel = Selector(text=location["hours"])
        oh = OpeningHours()
        for rule in sel.xpath("//tr"):
            day = sanitise_day(rule.xpath("./td/text()").get(), days=self.days)
            times = rule.xpath("./td/time/text()").get()
            if not day or not times:
                continue
            if times.lower() in ["closed"]:
                continue
            start_time, end_time = times.split("-")
            oh.add_range(day, start_time.strip(), end_time.strip(), time_format=self.time_format)

        return oh
