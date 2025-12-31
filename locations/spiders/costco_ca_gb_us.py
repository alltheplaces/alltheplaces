from typing import Iterable

from scrapy.http import Response
from unidecode import unidecode

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.hours import DAYS_FROM_SUNDAY, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS

# Don't specify a brand name so that NSI matching will pick the correct
# localised brand name.
COSTCO_SHARED_ATTRIBUTES = {"brand_wikidata": "Q715583"}


class CostcoCAGBUSSpider(JSONBlobSpider, CamoufoxSpider):
    name = "costco_ca_gb_us"
    item_attributes = {"brand": "Costco"} | COSTCO_SHARED_ATTRIBUTES
    allowed_domains = ["ecom-api.costco.com"]
    start_urls = [
        "https://ecom-api.costco.com/warehouseLocatorMobile/v1/warehouses.json?client_id=45823696-9189-482d-89c3-0c067e477ea1&latitude=0&longitude=0&limit=5000&distanceUnit=km"
    ]
    locations_key = "warehouses"
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("address"))
        if len(feature["name"]) > 0:
            feature["branch"] = feature["name"][0]["value"]
        feature.pop("name", None)

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature.get("warehouseId")
        item["branch"] = feature.get("branch")
        item["street_address"] = merge_address_lines([feature.get("line1"), feature.get("line2")])
        item["state"] = feature.get("territory")

        slug_branch_name = unidecode(item["branch"]).lower().replace(" ", "-")
        slug_city_name = unidecode(item["city"]).lower().replace(" ", "-")
        slug_state_code = None
        if item.get("state"):
            slug_state_code = item["state"].lower()
        if feature.get("subType") and feature["subType"].get("code") == "Business Center":
            # Costco allowing business customers
            if item["country"] == "US":
                # Reference: https://github.com/osmlab/name-suggestion-index/issues/11251
                item["name"] = "Costco Business Center"
            else:
                item["name"] = "Costco Business Centre"
            item["website"] = "https://www.costcobusinessdelivery.com/warehouse-locations/{}-{}-{}-{}.html".format(
                slug_branch_name, slug_city_name, slug_state_code, item["ref"]
            )
        else:
            # Costco allowing retail customers
            item["name"] = "Costco"
            if item["country"] == "US":
                item["website"] = "https://www.costco.com/warehouse-locations/{}-{}-{}.html".format(
                    slug_branch_name, slug_state_code, item["ref"]
                )
            elif item["country"] == "CA":
                item["website"] = "https://www.costco.ca/warehouse-locations/{}-{}-{}.html".format(
                    slug_branch_name, slug_state_code, item["ref"]
                )
            elif item["country"] == "GB":
                slug_branch_name = "".join(map(str.title, item["branch"].split())).removesuffix("Uk")
                item["website"] = "https://www.costco.co.uk/store-finder/{}".format(slug_branch_name)

        item["opening_hours"] = OpeningHours()
        for day_hours in feature.get("hours", []):
            if day_hours["title"][0]["value"].startswith("Business "):
                continue
            if "HOLIDAY" in day_hours["title"][0]["value"].upper():
                continue
            if day_hours["hoursType"]["code"] != "open":
                # Not observed to be any other value in a way this spider
                # would benefit from.
                continue
            for day_number in day_hours["weekDays"]:
                item["opening_hours"].add_range(
                    DAYS_FROM_SUNDAY[day_number - 1], day_hours["open"], day_hours["close"], "%H:%M:%S"
                )

        apply_category(Categories.SHOP_WHOLESALE, item)
        if opening_date := feature.get("openingDate"):
            item["extras"]["start_date"] = opening_date

        yield item
