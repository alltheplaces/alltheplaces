import json
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature

BRANDS = {
    "RocoMamas": ({"brand": "RocoMamas", "brand_wikidata": "Q123034964"}, Categories.RESTAURANT),
    "RocoGo": ({"brand": "RocoGo", "brand_wikidata": "Q123034964"}, Categories.FAST_FOOD),
}


class RocomamasSpider(SitemapSpider):
    name = "rocomamas"
    sitemap_urls = ["https://rocomamas.com/sitemap_index.xml"]
    sitemap_rules = [(r"/restaurants/[^/]+/[^/]+$", "parse_restaurant")]

    def deref_nuxt(self, data: list[Any], idx: int) -> Any:
        val = data[idx]
        if isinstance(val, dict):
            return {k: self.deref_nuxt(data, v) for k, v in val.items()}
        if isinstance(val, list):
            return [self.deref_nuxt(data, v) for v in val]
        return val

    def extract_brand_name(self, response: Response) -> str | None:
        for raw_ld in response.xpath('//script[@type="application/ld+json"]/text()').getall():
            ld = json.loads(raw_ld)
            for node in ld.get("@graph", [ld]):
                if node.get("@type") == "Restaurant":
                    return (node.get("brand") or {}).get("name")
        return None

    def parse_restaurant(self, response: Response) -> Iterable[Feature]:
        raw = response.xpath('//script[@id="__NUXT_DATA__"]/text()').get()
        if not raw:
            return

        slug = response.url.rstrip("/").split("/")[-1]
        data = json.loads(raw)
        shop_idx = next(
            (
                i
                for i, obj in enumerate(data)
                if isinstance(obj, dict) and "slug" in obj and "hours" in obj and data[obj["slug"]] == slug
            ),
            None,
        )
        if shop_idx is None:
            return

        shop = self.deref_nuxt(data, shop_idx)
        item = DictParser.parse(shop)
        item["ref"] = shop["key"]
        item["website"] = response.url

        if item.get("postcode") in {"9000", "9999", "0000", "00000"}:
            item.pop("postcode")

        brand_name = self.extract_brand_name(response)
        if brand_info := BRANDS.get(brand_name):
            brand_details, category = brand_info
            item.update(brand_details)
            apply_category(category, item)
        amenities = shop.get("amenities") or {}
        apply_yes_no(Extras.HALAL, item, amenities.get("halaal") is True)
        apply_yes_no(Extras.WIFI, item, amenities.get("wifi") is True)
        item["branch"] = item.pop("name").removeprefix(item.get("brand", "")).strip()

        if hours := shop.get("hours"):
            item["opening_hours"] = OpeningHours()
            for day in hours:
                if day.get("closed"):
                    item["opening_hours"].set_closed(day["day"])
                elif day.get("open") and day.get("close"):
                    item["opening_hours"].add_range(day["day"], day["open"], day["close"], time_format="%H:%M:%S")

        yield item
