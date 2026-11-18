import json
import re
from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, TextResponse
from unidecode import unidecode

from locations.categories import Categories, PaymentMethods, apply_category, apply_yes_no
from locations.items import Feature
from locations.storefinders.uberall import UberallSpider

# Slug rules of the Todis store finder's hash routes (#!/l/{city}/{street}/{id}),
# replicated so that website values match the widget's own URLs.
SLUG_PUNCTUATION = re.compile(r"[\\.,/#!$%^&*|;:{}=\-_`'~()\[\]]")
SLUG_WHITESPACE = re.compile(r"\s+")


class TodisITSpider(UberallSpider):
    name = "todis_it"
    item_attributes = {"brand": "Todis", "brand_wikidata": "Q3992174", "name": "Todis"}
    allowed_domains = ["uberall.com"]
    key = "BWr7teQp5Na9Ikhj3y3pvORJS9OG5M"
    locations_api_url = f"https://uberall.com/api/storefinders/{key}/locations"

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(url=f"{self.locations_api_url}/all", callback=self.parse_store_list)

    def parse_store_list(self, response: TextResponse) -> Iterable[JsonRequest]:
        # /locations/all lacks per-store email, so the detail endpoint (which
        # has it) is fetched per store.
        for location in response.json()["response"]["locations"]:
            yield JsonRequest(
                url=f"{self.locations_api_url}/{location['id']}?language=it",
                callback=self.parse_store,
            )

    def parse_store(self, response: TextResponse) -> Iterable[Feature]:
        location = response.json()["response"]
        # Reuse the parent list parser on a single-location envelope.
        body = json.dumps({"status": "SUCCESS", "response": {"locations": [location]}}, ensure_ascii=False)
        yield from self.parse(response.replace(body=body.encode("utf-8")))

    def post_process_item(self, item: Feature, response: TextResponse, location: dict) -> Iterable[Feature]:
        # The API name ("Todis - Supermercato (City - Street)") only repeats the address.
        item.pop("name")

        item["website"] = "https://www.todis.it/negozi-e-volantini/#!/l/{}/{}/{}".format(
            self.url_slug(location["city"]),
            self.url_slug(location["streetAndNumber"]),
            location["id"],
        )
        item["image"] = next(
            (photo["publicUrl"] for photo in location.get("photos") or [] if photo.get("type") == "MAIN"),
            None,
        )

        apply_yes_no(PaymentMethods.CASH, item, True)
        apply_yes_no(PaymentMethods.CARDS, item, True)
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item

    @staticmethod
    def url_slug(value: str) -> str:
        slug = SLUG_PUNCTUATION.sub(" ", value.lower().strip())
        slug = unidecode(SLUG_WHITESPACE.sub("-", slug))
        return slug or "-"
