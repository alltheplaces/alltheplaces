from urllib.parse import urljoin

from scrapy.http import Response

from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class StorageKingAUNZSpider(JSONBlobSpider):
    name = "storage_king_au_nz"
    item_attributes = {"brand": "Storage King", "brand_wikidata": "Q114353097"}
    start_urls = [
        "https://www.storageking.com.au/apps/checkout/api/facility/all",
        "https://www.storageking.co.nz/apps/checkout/api/facility/all",
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item: Feature, response: Response, feature: dict):
        if feature["is_active"] is False:
            return
        item["name"] = None
        item["street_address"] = item.pop("addr_full")
        item["branch"] = feature.get("short_name")
        item["geometry"] = feature["Location"]
        item["website"] = urljoin(
            (
                "https://www.storageking.com.au/collections/"
                if ".com.au" in response.url
                else "https://www.storageking.co.nz/collections/"
            ),
            feature["collection_handle"],
        )

        item["opening_hours"] = self.parse_oh(feature.get("trading_hours", {}).get("accessHours", {}))
        item["extras"]["opening_hours:office"] = self.parse_oh(
            feature.get("trading_hours", {}).get("officeHours", {})
        ).as_opening_hours()

        yield item

    def parse_oh(self, rules: dict) -> OpeningHours:
        oh = OpeningHours()
        if rules:
            for day, rule in rules.items():
                if rule["closed"] is True:
                    oh.set_closed(day)
                else:
                    oh.add_range(day, rule["from"], rule["to"])
        return oh
