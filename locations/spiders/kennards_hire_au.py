from typing import Iterable
from urllib.parse import urlparse

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class KennardsHireAUSpider(JSONBlobSpider):
    name = "kennards_hire_au"
    item_attributes = {"brand": "Kennards Hire", "brand_wikidata": "Q63557330"}
    allowed_domains = ["www.kennards.com.au"]
    start_urls = ["https://www.kennards.com.au/api/data/branches"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if not feature.get("latitude") or not feature.get("longitude"):
            # Not a valid plant hire location - head office/warehouse/etc
            return

        item["ref"] = str(feature["code"])
        item["branch"] = item.pop("name", None)
        item["street_address"] = merge_address_lines(
            [feature["address"].get("streetLine1"), feature["address"].get("streetLine2")]
        )
        item["city"] = feature["address"].get("suburb")
        item["state"] = feature["address"].get("state")
        item["postcode"] = feature["address"].get("postcode")
        item["country"] = feature["address"].get("country")
        if website_path := feature.get("url"):
            item["website"] = "https://" + urlparse(response.url).netloc + website_path

        item["opening_hours"] = OpeningHours()
        for day_hours in feature.get("workingHours", []):
            if day_hours["title"] not in DAYS_FULL:
                continue
            if not day_hours.get("openingTime") or not day_hours.get("closingTime"):
                item["opening_hours"].set_closed(day_hours["title"])
                continue
            item["opening_hours"].add_range(
                day_hours["title"], day_hours["openingTime"], day_hours["closingTime"], "%I:%M%p"
            )

        apply_category(Categories.SHOP_PLANT_HIRE, item)

        yield item
