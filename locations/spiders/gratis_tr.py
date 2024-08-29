import re

import scrapy
import scrapy.http

from locations.categories import apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.pipelines.address_clean_up import clean_address


class GratisTRSpider(scrapy.Spider):
    name = "gratis_tr"
    start_urls = [
        "https://api.cn94v1klbw-gratisicv1-p1-public.model-t.cc.commerce.ondemand.com/gratiscommercewebservices/v2/gratis/stores/country/TR?fields=DEFAULT&lang=tr&curr=TRY"
    ]
    item_attributes = {"brand": "Gratis", "brand_wikidata": "Q28605813"}

    def start_requests(self):
        yield scrapy.Request(headers={"Accept": "application/json"}, url=self.start_urls[0], callback=self.parse)

    def parse(self, response):
        for store in response.json()["pointOfServices"]:
            item = DictParser.parse(store)
            if item["lat"] is None or item["lon"] is None:
                # SKIP: No coordinates means either the store is closed or this is an office
                continue
            item["ref"] = store["storeCode"]
            item["city"] = get_loop(["address", "townInfo", "name"], store)
            item["state"] = get_loop(["address", "cityInfo", "name"], store)
            item["branch"] = store["displayName"]
            street_address, addr_full = self.process_address(
                get_loop(["address", "line1"], store), item["city"], item["state"]
            )
            item["addr_full"] = addr_full
            item["street_address"] = street_address
            item["name"] = "Gratis"
            # Gratis has a default opening hours of 10:00 - 22:00
            # For every store scraped with its own web page, the opening hours is the same
            oh = OpeningHours()
            oh.add_days_range(DAYS, "10:00", "22:00")
            item["opening_hours"] = oh.as_opening_hours()
            apply_category({"brand:website": "https://www.gratis.com"}, item)

            if item["city"] is not None and item["state"] is not None:
                apply_category({"website": self.get_page_url(item["branch"], item["city"], item["state"])}, item)
            if store.get("phone") is not None and store.get("phone") != "-":
                item["phone"] = store["phone"]

            yield item

    # The only added information is opening hours but all stores have the same opening hours so this is not used
    # For future reference, this is how the opening hours are scraped
    def parse_page(self, response: scrapy.http.TextResponse):
        time_re = re.compile("([0-9]|0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])")
        time_str = response.css("span.store-times-content").get()
        oh = OpeningHours()
        if time_str is not None:
            [opening, closing] = list(map(lambda e: f"{e[0]}:{e[1]}", time_re.findall(time_str)))
            oh.add_days_range(DAYS, opening, closing)
        item = response.meta["item"]
        item["opening_hours"] = oh.as_opening_hours()
        yield item

    @staticmethod
    def process_address(address: str, district: str | None = None, province: str | None = None) -> tuple[str, str]:
        cleaned_street_adress = clean_address(address.strip().removesuffix(f"/{district}").strip())
        cleaned_addr_full = clean_address([cleaned_street_adress, district, province])
        return cleaned_street_adress, cleaned_addr_full

    @staticmethod
    def get_page_url(display_name: str, district: str, province: str) -> str:
        display_name = "-".join(map(lambda e: GratisTRSpider.process_for_url(e.strip()), display_name.split(" ")))
        district = "-".join(map(lambda e: GratisTRSpider.process_for_url(e.strip()), display_name.split(" ")))
        province = GratisTRSpider.process_for_url(province)
        url = "https://www.gratis.com/magazalarimiz/{province}/{district}/{display_name}"
        return url.format(province=province, district=district, display_name=display_name)

    @staticmethod
    def process_for_url(s: str) -> str:
        chars_dict = {"İ": "i", "Ğ": "g", "Ü": "u", "Ş": "s", "Ö": "o", "Ç": "c"}
        for char, replacement in chars_dict.items():
            s = s.replace(char, replacement)
        return s.lower()


def get_loop(keys: list[str], d: dict):
    for key in keys:
        d = d.get(key)
        if d is None:
            return None

    return d
