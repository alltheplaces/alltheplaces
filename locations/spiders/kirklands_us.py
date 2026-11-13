import json
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class KirklandsUSSpider(Spider):
    """
    Kirkland's stores are listed on Bed Bath & Beyond's site since the two companies joined in
    2025; kirklands.com no longer has store pages. The one page carries every store of three
    brands as JSON, with a brand legend: 1 Bed Bath & Beyond, 2 Kirkland's, 3 The Container
    Store, and "1|3" for a store shared by Bed Bath & Beyond and The Container Store.
    """

    name = "kirklands_us"
    item_attributes = {"brand": "Kirkland's", "brand_wikidata": "Q6415714"}
    start_urls = ["https://www.bedbathandbeyond.com/store-locations"]
    # The site stalls requests that do not look like a browser's.
    user_agent = BROWSER_DEFAULT
    custom_settings = {"DOWNLOAD_TIMEOUT": 60}
    brand_ids = {"2"}

    def parse(self, response: TextResponse, **kwargs: Any) -> Iterable[Feature]:
        data = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        sections = data["props"]["pageProps"]["aggData"]["marketing_dynamic_page"]["page_contentConnection"]["edges"]
        for section in sections:
            for entry in section["node"].get("stores") or []:
                store = entry["store"]
                if not self.brand_ids & set(store["brand_id"].split("|")):
                    continue
                item = DictParser.parse(store)
                item.pop("addr_full", None)
                item["street_address"] = store["street_address"]
                item["branch"] = item.pop("name", None)
                item["ref"] = f"{store['brand_id']}-{store['zip']}-{store['street_address']}".lower()
                item["opening_hours"] = OpeningHours()
                for days, key in (
                    ("Mo-Th", "monday_thursday_hours"),
                    ("Fr", "friday_hours"),
                    ("Sa", "saturday_hours"),
                    ("Su", "sunday_hours"),
                ):
                    if hours := store.get(key):
                        item["opening_hours"].add_ranges_from_string(f"{days} {hours}")
                yield from self.post_process_item(item, store)

    def post_process_item(self, item: Feature, store: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_INTERIOR_DECORATION, item)
        yield item
