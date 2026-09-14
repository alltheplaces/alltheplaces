from scrapy import Request
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class LauraSecordCASpider(JSONBlobSpider):
    name = "laura_secord_ca"
    item_attributes = {
        "brand": "Laura Secord",
        "brand_wikidata": "Q6499418",
        "name": "Laura Secord",
    }
    start_urls = ["https://store.laurasecord.ca/api/store/forsite"]
    locations_key = "data"

    async def start(self):
        # The API rejects requests that don't carry an Origin/Referer matching the site that embeds it.
        headers = {
            "Origin": "https://laurasecord.ca",
            "Referer": "https://laurasecord.ca/find-a-store/",
        }
        for url in self.start_urls:
            yield Request(url, headers=headers)

    def pre_process_data(self, feature: dict) -> None:
        if feature.get("street2"):
            feature["street"] = feature["street"] + ", " + feature["street2"]

        # Canadian postcodes are returned without the conventional separating space, e.g. "K1H8K2".
        if (postcode := feature.get("postal_code")) and len(postcode) == 6:
            feature["postal_code"] = postcode[:3] + " " + postcode[3:]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict):
        if feature.get("closed_perm"):
            return  # permanently closed, do not yield

        item["branch"] = item.pop("name", "")
        item["ref"] = feature.get("store_id")

        if not feature.get("closed_temp"):
            item["opening_hours"] = self.parse_hours(feature.get("business_hour") or [])

        apply_category(Categories.SHOP_CHOCOLATE, item)

        yield item

    @staticmethod
    def parse_hours(rules: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules:
            day = DAYS[rule["weekday_number"] - 1]
            if rule.get("close"):
                oh.set_closed(day)
            else:
                oh.add_range(day, rule["start"], rule["stop"], time_format="%Hh%M")
        return oh
