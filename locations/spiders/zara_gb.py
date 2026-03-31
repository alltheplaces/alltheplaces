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

        oh = OpeningHours()
        for day_time in feature["openingHours"]:
            for open_close_time in day_time["openingHoursInterval"]:
                oh.add_range(
                    DAYS_FULL[day_time["weekDay"] - 1], open_close_time["openTime"], open_close_time["closeTime"]
                )
        item["opening_hours"] = oh

        apply_category(Categories.SHOP_CLOTHES, item)

        yield item
