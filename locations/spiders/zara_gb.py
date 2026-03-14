from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Clothes, apply_category, apply_clothes
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class ZaraGBSpider(JSONBlobSpider):
    name = "zara_gb"
    item_attributes = {"brand": "Zara", "brand_wikidata": "Q147662"}
    start_urls = [
        "https://www.zara.com/uk/en/stores-locator/extended/search?lat=53.5072178&lng=-1.1275862&isDonationOnly=false&showOnlyPickup=false&showStoresCapacity=false&radius=1000&ajax=true"
    ]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DEFAULT_REQUEST_HEADERS": {
            "Host": "www.zara.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:143.0) Gecko/20100101 Firefox/143.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Connection": "keep-alive",
        },
    }
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
        item["street_address"] = " ".join(feature["addressLines"])
        item["opening_hours"] = OpeningHours()
        if len(feature["openingHours"]) > 0:
            for i in range(7):
                item["opening_hours"].add_range(
                    DAYS[i],
                    feature["openingHours"][i]["openingHoursInterval"][0]["openTime"],
                    feature["openingHours"][i]["openingHoursInterval"][0]["closeTime"],
                )
        yield item
