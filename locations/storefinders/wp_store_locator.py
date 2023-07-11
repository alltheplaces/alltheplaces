from scrapy import Selector, Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours, sanitise_day
from locations.items import Feature
from locations.spiders.vapestore_gb import clean_address

# Source code for the WP Store Locator API call used by this spider:
# https://github.com/wp-plugins/wp-store-locator/blob/master/frontend/wpsl-ajax-functions.php
#
# To use this store finder, specify allowed_domains = [x, y, ..]
# (either one or more domains such as example.net) and the default
# path for the WP Store Locator API endpoint will be used.
# In the event the default path is different, you can alternatively
# specify one or more start_urls = [x, y, ..].
#
# If clean ups or additional field extraction is required from the
# source data, override the parse_item function. Two parameters are
# passed, item (an ATP "Feature" class) and location (a dict which
# is returned from the store locator JSON response for a particular
# location).
#
# Important note: this store locator has a hard-coded "max_results"
# attribute set server-side, that can be configured differently for
# each installation and cannot be overridden client-side. Check the
# number of results returned and if it is a round number (e.g. 50)
# apply caution and double check this is the full count. If results
# are truncated, you will need to stop using WPStoreLocatorSpider
# and instead use another approach for scraping locations.


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
