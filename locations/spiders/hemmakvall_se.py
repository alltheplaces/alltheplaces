import re
from html import unescape

from scrapy import Selector

from locations.hours import DAYS_SE, OpeningHours
from locations.storefinders.store_locator_plus_self import StoreLocatorPlusSelfSpider


class HemmakvallSESpider(StoreLocatorPlusSelfSpider):
    name = "hemmakvall_se"
    item_attributes = {"brand": "Hemmakväll", "brand_wikidata": "Q10521791"}
    allowed_domains = ["www.hemmakvall.se"]
    iseadgg_countries_list = ["SE"]
    search_radius = 200
    max_results = 75

    def parse_item(self, item, location):
        item.pop("website", None)
        hours_string = " ".join(Selector(text=unescape(location["hours"])).xpath("//text()").getall())
        hours_string = re.sub(r"\s+", " ", hours_string)
        hours_string = re.sub(r"(?<=\d) ?- ?(?=\d)", "-", hours_string)
        hours_string = re.sub(r"(?<![\d:])(?: | ?- ?)(?=\d)", ": ", hours_string)
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string, days=DAYS_SE)
        yield item
