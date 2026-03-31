from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Clothes, apply_category, apply_clothes
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import BROWSER_DEFAULT


class ZaraGBSpider(JSONBlobSpider):
    name = "zara_gb"
    item_attributes = {"brand": "Zara", "brand_wikidata": "Q147662"}
    start_urls = [
        "https://www.zara.com/uk/en/stores-locator/extended/search?lat=53.5072178&lng=-1.1275862&isDonationOnly=false&showOnlyPickup=false&showStoresCapacity=false&radius=1000&ajax=true"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}
    drop_attributes = {"facebook", "twitter"}
    requires_proxy = True

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        apply_category(Categories.SHOP_CLOTHES, item)
        if "Woman" in feature.get("sections", []):
            apply_clothes([Clothes.WOMEN], item)
        if "Man" in feature.get("sections", []):
            apply_clothes([Clothes.MEN], item)
        if "Kids" in feature.get("sections", []):
            apply_clothes([Clothes.CHILDREN], item)
        item["street_address"] = merge_address_lines(feature["addressLines"])

        try:
            item["opening_hours"] = self.parse_hours(feature["openingHours"])
        except:
            pass

        apply_category(Categories.SHOP_CLOTHES, item)

        yield item

    def parse_hours(self, rules: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules:
            for times in rule["openingHoursInterval"]:
                oh.add_range(DAYS_FULL[rule["weekDay"] - 1], times["openTime"], times["closeTime"])
        return oh
