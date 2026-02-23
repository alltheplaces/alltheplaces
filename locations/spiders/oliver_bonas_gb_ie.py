import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class OliverBonasGBIESpider(Spider):
    name = "oliver_bonas_gb_ie"
    item_attributes = {"brand": "Oliver Bonas", "brand_wikidata": "Q65045195"}
    start_urls = ["https://www.oliverbonas.com/api/n/find?type=store&filter={}&verbosity=1"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["catalog"]:
            item = Feature()
            item["ref"] = store["id"]
            item["branch"] = re.sub(r"\s*Oliver Bonas (Outlet )?Store\b.*$", "", store.get("store_name", ""))
            if "Oliver Bonas Outlet" in store.get("store_name", ""):
                item["name"] = "Oliver Bonas Outlet"
            item["street_address"] = store.get("address")
            item["city"] = store.get("city")
            item["state"] = store.get("state")
            item["postcode"] = store.get("postcode")
            item["country"] = store.get("country_id")
            item["lat"] = store.get("latitude")
            item["lon"] = store.get("longitude")
            item["phone"] = store.get("phone")

            apply_category(Categories.SHOP_CLOTHES, item)

            if url := store.get("url"):
                item["website"] = f"https://www.oliverbonas.com{url}"
                yield response.follow(url, self.parse_store, cb_kwargs={"item": item})
            else:
                yield item

    def parse_store(self, response: Response, item: Feature) -> Any:
        oh = OpeningHours()
        hours_text = response.xpath("//h3[contains(text(),'Opening times')]/following-sibling::ul[1]//text()").getall()
        oh.add_ranges_from_string(" ".join(hours_text))
        item["opening_hours"] = oh
        yield item
