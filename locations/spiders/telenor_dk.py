import re
from typing import AsyncIterator, Iterable
from urllib.parse import urljoin

from scrapy import Selector, Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_DK, NAMED_DAY_RANGES_DK, OpeningHours
from locations.items import Feature


class TelenorDKSpider(Spider):
    name = "telenor_dk"
    allowed_domains = ["www.telenor.dk", "telenor.dk"]
    item_attributes = {
        "brand": "Telenorbutikken",
        "brand_wikidata": "Q845632",
        "country": "DK",
    }
    custom_settings = {"ROBOTSTXT_OBEY": False}
    no_refs = True

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://www.telenor.dk/da/sharedblock/2ed9d2b7-45d2-4f7d-9406-a933d6883cdc/FindNearestShopBlock/GetShops/2bd5f376-3f79-475b-aa1e-b45174b9a2f3/",
            headers={"X-Requested-With": "XMLHttpRequest"},
        )

    def parse(self, response) -> Iterable[Feature]:
        for store in response.json():
            item = DictParser.parse(store)

            # ID 2 (Telenor stores)
            # ID 3 (Telenor store inside Bilka)
            # ID 4 (Elgiganten stores)
            if store_type_id := str(store.get("type").get("id")):
                if store_type_id not in {"2", "3"}:
                    continue
                if store_type_id == "3":
                    item["located_in"] = "Bilka"

            html = Selector(text=store.get("html"))

            address_lines = [
                line.strip() for line in html.xpath("//div/div/div[1]/div/p/text()").getall() if line and line.strip()
            ]
            if address_lines:
                item["addr_full"] = re.sub(r"\s+", " ", ", ".join(address_lines))

            if phone := html.xpath("//div/div/div[2]/p[1]/text()").get():
                item["phone"] = phone.replace("Telefon:", "").strip()

            if hours_string := " ".join(html.xpath("//div/div/div[3]/div//text()").getall()).strip():
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string(
                    hours_string, days=DAYS_DK, named_day_ranges=NAMED_DAY_RANGES_DK
                )

            if website := item.get("website"):
                item["website"] = urljoin("https://telenor.dk", website)

            apply_category(Categories.SHOP_MOBILE_PHONE, item)
            yield item
