import json
import re

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class PelotonSpider(Spider):
    name = "peloton"
    item_attributes = {"brand": "Peloton", "brand_wikidata": "Q56276186"}
    start_urls = ["https://stores.onepeloton.com/en-US/peloton-store-locations"]

    def parse(self, response):
        yield from response.follow_all(css="a.listing-list__store__overlay-link", callback=self.parse_store)

    def parse_store(self, response):
        store = json.loads(response.css(".DetailMap::attr(data-listing)").get())
        if store["virtual_location"] or store["store_type"] != "peloton":
            return
        item = Feature(
            ref=store["id"],
            branch=store["name"].removeprefix("Peloton "),
            street_address=store["address_1"],
            city=store["city"],
            state=store["state"],
            postcode=store["zip"],
            country=store["country"],
            lat=store["latitude"],
            lon=store["longitude"],
            phone=store["phone"],
            email=store["email"],
            website=response.url,
        )
        if store["hours"]:
            hours = re.sub(r"(?<=\d)([ap])\b", r"\1m", store["hours"])
            hours = re.sub(r"\bM-", "Mon-", hours)
            # Some retail hours omit AM/PM, e.g. "10-9" and "11-8p".
            hours = re.sub(r"\b(\d{1,2})-(\d{1,2})(pm)?\b", r"\1am-\2pm", hours)
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours)
        apply_category(Categories.SHOP_SPORTS, item)
        yield item
