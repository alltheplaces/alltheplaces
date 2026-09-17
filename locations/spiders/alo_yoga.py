from typing import Any, AsyncIterator, Iterable

from scrapy import Selector
from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines

# The API caps a response at 100 entries.
PAGE_SIZE = 100


class AloYogaSpider(Spider):
    name = "alo_yoga"
    item_attributes = {"brand": "Alo Yoga", "brand_wikidata": "Q123700068"}
    # Public read key, taken from the page source of /pages/stores.
    api_key = "aa96744e7fe74e2a90d22918299c1f1d"

    def make_request(self, offset: int) -> JsonRequest:
        return JsonRequest(
            url="https://cdn.builder.io/api/v3/content/store"
            f"?apiKey={self.api_key}&limit={PAGE_SIZE}&offset={offset}&noTargeting=true",
            cb_kwargs=dict(offset=offset),
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.make_request(0)

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature | JsonRequest]:
        stores = response.json()["results"]
        for store in stores:
            location = store["data"]
            if "coming soon" in location["name"].lower():
                continue

            item = Feature()
            item["ref"] = store["id"]
            item["branch"] = location["name"].strip()
            item["phone"] = (location.get("phone") or "").strip()
            # "CA" here is California, not Canada, so only the leading city is safe.
            item["city"] = location["city"].split(",")[0].strip()

            # Place links carry coordinates, search links only the address.
            address = Selector(text=location["location"])
            item["addr_full"] = merge_address_lines(address.xpath("//text()").getall())
            extract_google_position(item, address)

            item["opening_hours"] = OpeningHours()
            for rule in Selector(text=location.get("hours") or "").xpath("//p"):
                item["opening_hours"].add_ranges_from_string(rule.xpath("normalize-space(.)").get())

            apply_category(Categories.SHOP_CLOTHES, item)
            yield item

        if len(stores) == PAGE_SIZE:
            yield self.make_request(kwargs["offset"] + PAGE_SIZE)
