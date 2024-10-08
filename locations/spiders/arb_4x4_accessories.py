from scrapy import Selector, Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class Arb4x4AccessoriesSpider(Spider):
    name = "arb_4x4_accessories"
    item_attributes = {
        "brand": "ARB 4×4 Accessories",
        "brand_wikidata": "Q126166453",
        "extras": Categories.SHOP_CAR_PARTS.value,
    }
    allowed_domains = ["www.arb.com.au"]
    start_urls = ["https://www.arb.com.au/wp-content/themes/arb_2017/assets/inc/json/stores.json"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json():
            if not location.get("is_arb_store") and not location.get("is_arb_corporate_store"):
                continue  # Ignore resellers.

            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full", None)

            if (
                item["website"]
                and not item["website"].startswith("www.")
                and not item["website"].startswith("https://")
                and not item["website"].startswith("http://")
            ):
                item["website"] = "https://www.arb.com.au" + item["website"]
            elif item["website"].startswith("www."):
                item["website"] = "https://" + item["website"]

            if item["name"].startswith("ARB 4×4 Accessories "):
                item["branch"] = item["name"].replace("ARB 4×4 Accessories ", "")

            hours_string = " ".join(
                filter(None, map(str.strip, Selector(text=location.get("opening_hours")).xpath("//text()").getall()))
            )
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)

            yield item
