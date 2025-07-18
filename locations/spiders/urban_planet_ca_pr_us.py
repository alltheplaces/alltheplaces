from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class UrbanPlanetCAPRUSSpider(JSONBlobSpider):
    name = "urban_planet_ca_pr_us"
    allowed_domains = ["urban-planet.com"]
    start_urls = ["https://urban-planet.com/apps/api/v1/stores"]
    locations_key = "stores"
    brands = {
        "Forever 21": {"brand": "Forever 21", "brand_wikidata": "Q1060537"},
        "Sirens": {"brand": "Sirens", "brand_wikidata": "Q123410104"},
        "Stitches": {"brand": "Stitches", "brand_wikidata": "Q7617652"},
        "Urban Behavior": {"brand": "Urban Behavior", "brand_wikidata": "Q7899859"},
        "Urban Behaviour": {"brand": "Urban Behavior", "brand_wikidata": "Q7899859"},
        "Urban Kids": {"brand": "Urban Kids", "brand_wikidata": "Q133255740"},
        "Urban Planet": {"brand": "Urban Planet", "brand_wikidata": "Q112965875"},
    }

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        brand_name = feature["brand"].strip()
        if brand_name not in self.brands.keys():
            self.logger.warning(
                "Unknown brand '{}'. Feature extracted without brand_wikidata set. Spider needs updating to map the brand to a Wikidata item.".format(
                    brand_name
                )
            )
            item["brand"] = brand_name
        else:
            item["brand"] = self.brands[brand_name]["brand"]
            item["brand_wikidata"] = self.brands[brand_name]["brand_wikidata"]
        item["website"] = "https://urban-planet.com/pages/" + feature["store_handle"]
        self.parse_additional_fields(item, feature)
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item

    @staticmethod
    def parse_additional_fields(item: Feature, feature: dict) -> None:
        # Parsing function split out for re-use by other spiders of YM Inc.
        # brands that re-use this same storefinder.
        item["lat"] = feature["address"]["latitude"]
        item["lon"] = feature["address"]["longitude"]
        item["branch"] = feature["address"]["name"]
        item["street_address"] = merge_address_lines(
            [feature["address"].get("line1"), feature["address"].get("line2"), feature["address"].get("line3")]
        )
        item["opening_hours"] = OpeningHours()
        for day_hours in feature["open_hours"]:
            if "closed" in day_hours.keys():
                item["opening_hours"].set_closed(day_hours["day"])
            else:
                item["opening_hours"].add_range(day_hours["day"], day_hours["open_time"], day_hours["close_time"])
