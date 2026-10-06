from typing import Any, Iterable

from scrapy.http import TextResponse

from locations.items import Feature
from locations.storefinders.wp_go_maps import WpGoMapsSpider


class BauspeziDESpider(WpGoMapsSpider):
    name = "bauspezi_de"
    item_attributes = {"brand": "BauSpezi", "brand_wikidata": "Q85324366"}
    allowed_domains = ["bauspezi.de"]
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"X-Requested-With": "XMLHttpRequest"}}

    def parse(self, response: TextResponse, **kwargs: Any) -> Iterable[Feature]:
        seen = set()
        for item in self.parse_stores(response):
            if (item["lat"], item["lon"]) in seen:
                continue
            seen.add((item["lat"], item["lon"]))
            yield item

    def post_process_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        # Category 2 is "Verbundpartner", associated merchants which are not BauSpezi stores
        if "2" in location.get("categories", []):
            return
        item.pop("name", None)
        custom_fields = {field["name"]: field["value"] for field in location.get("custom_field_data", [])}
        item["email"] = custom_fields.get("E-Mail-Adresse")
        item["phone"] = custom_fields.get("Telefon")
        item["website"] = location.get("link")
        yield item
