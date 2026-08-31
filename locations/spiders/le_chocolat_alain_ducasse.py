from typing import AsyncIterator, Iterable

import scrapy
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature

# Generic head-office contact address shared across many locations; not
# branch-specific, so it is not used as a per-store email.
GENERIC_EMAIL = "contact@lechocolat-alainducasse.com"


class LeChocolatAlainDucasseSpider(scrapy.Spider):
    name = "le_chocolat_alain_ducasse"
    item_attributes = {"brand": "Le Chocolat Alain Ducasse", "brand_wikidata": "Q114374063"}
    allowed_domains = ["www.lechocolat-alainducasse.com"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://www.lechocolat-alainducasse.com/fr/module/sym_partoo/ajax?action=GetStores&ajax=1&search=&country=&manufacture=",
            callback=self.parse,
        )

    def parse(self, response: Response) -> Iterable[Feature]:
        for store in response.json().get("stores", []):
            if store.get("status") != "open":
                continue

            item = Feature()
            item["ref"] = store["id"]
            item["name"] = store.get("name", "").strip()
            item["lat"] = store.get("lat")
            item["lon"] = store.get("long")
            item["street_address"] = store.get("address_full")
            item["country"] = store.get("country")

            # City names are given in French regardless of country (e.g. "Londres"
            # for London), so translate the handful of known non-French exonyms.
            item["city"] = {"Londres": "London"}.get(store.get("city"), store.get("city"))

            # zipcode is numeric JSON for FR/DE, losing any leading zero (e.g. Nice's
            # "06300" arrives as 6300); it's a non-numeric string as-is for GB.
            postcode = str(store.get("zipcode") or "").strip()
            if postcode.isdigit() and item["country"] in ("FR", "DE"):
                postcode = postcode.zfill(5)
            item["postcode"] = postcode

            item["website"] = store.get("website_url") or response.urljoin(f"/fr/magasins#{store['id']}")

            if contact := (store.get("contacts") or [{}])[0]:
                if phones := contact.get("phone_numbers"):
                    item["phone"] = str(phones[0])
                if (email := contact.get("email")) and email != GENERIC_EMAIL:
                    item["email"] = email

            item["opening_hours"] = self.parse_hours(store.get("open_hours") or {})

            apply_category(Categories.SHOP_CHOCOLATE, item)

            yield item

    @staticmethod
    def parse_hours(open_hours: dict) -> OpeningHours:
        oh = OpeningHours()
        for day, ranges in open_hours.items():
            for time_range in ranges:
                open_time, _, close_time = time_range.partition("-")
                oh.add_range(day, open_time, close_time)
        return oh
