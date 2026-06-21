from typing import Iterable
from urllib.parse import urlencode

from scrapy.http import JsonRequest

from locations.brand_utils import extract_located_in
from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.spiders.circle_k import CircleKSpider
from locations.spiders.cvs_us import PHARMACY_BRANDS as CVS_BRANDS
from locations.spiders.h_e_b_us import HEBUSSpider
from locations.spiders.murphy_usa_us import BRANDS as MURPHY_USA_BRANDS
from locations.spiders.valero import ValeroSpider
from locations.spiders.walgreens import WalgreensSpider
from locations.spiders.walmart_us import WalmartUSSpider
from locations.storefinders.yext_search import YextSearchSpider


class FrostBankUSSpider(YextSearchSpider):
    name = "frost_bank_us"
    item_attributes = {"brand": "Frost Bank", "brand_wikidata": "Q5506152"}
    host = "https://locations.frostbank.com"
    search_types = ("LOCATION", "ATM")
    search_radius = 500
    future_location_filters = {"Coming Soon", "Planned"}
    generic_phone = "+18005137678"
    LOCATED_IN_MAPPINGS = [
        (["Circle K"], CircleKSpider.CIRCLE_K),
        (["CVS"], CVS_BRANDS["CVS Pharmacy"]),
        (["Central Market"], {"brand": "Central Market", "brand_wikidata": "Q5061401"}),
        (["H-E-B", "HEB"], HEBUSSpider.item_attributes),
        (["Murphy"], MURPHY_USA_BRANDS["Murphy USA"]),
        (["Valero"], ValeroSpider.item_attributes),
        (["Walgreens"], WalgreensSpider.WALGREENS),
        (["Walmart"], WalmartUSSpider.item_attributes),
    ]

    def make_request(self, offset: int) -> JsonRequest:
        query = urlencode(
            {
                "type": self.search_types,
                "r": self.search_radius,
                "per": self.page_size,
                "offset": offset,
            },
            doseq=True,
        )
        return JsonRequest(
            url=f"{self.host}/search?{query}",
            headers={"Accept": "application/json"},
        )

    def parse_item(self, location: dict, item: Feature) -> Iterable[Feature]:
        profile = location["profile"]
        if profile.get("closed") or self.is_future_location(profile):
            return

        item["ref"] = profile["meta"]["id"]
        if phone := item.get("phone"):
            phones = [phone.strip() for phone in phone.split(";") if phone.strip() != self.generic_phone]
            if phones:
                item["phone"] = "; ".join(phones)
            else:
                item.pop("phone", None)
        item.pop("email", None)

        if profile.get("c_bankLocationType") == "Branch":
            item.pop("name", None)
            item["branch"] = profile.get("c_branchName")
            apply_category(Categories.BANK, item)
            apply_yes_no(Extras.ATM, item, bool(profile.get("c_aTMHours")))
            if atm_hours := self.parse_opening_hours(profile.get("c_aTMHours")).as_opening_hours():
                item["extras"]["opening_hours:atm"] = atm_hours
        elif profile.get("c_bankLocationType") == "ATM":
            item.pop("branch", None)
            item.pop("website", None)
            apply_category(Categories.ATM, item)
            item["located_in"], item["located_in_wikidata"] = extract_located_in(
                item.get("name", ""),
                self.LOCATED_IN_MAPPINGS,
            )
            item.pop("name", None)
        else:
            self.crawler.stats.inc_value(f"atp/{self.name}/unknown_location_type/{profile.get('c_bankLocationType')}")
            return

        if not item.get("opening_hours").as_opening_hours():
            item.pop("opening_hours", None)

        yield item

    def is_future_location(self, profile: dict) -> bool:
        return bool(self.future_location_filters.intersection(profile.get("c_locatorFilters", [])))
