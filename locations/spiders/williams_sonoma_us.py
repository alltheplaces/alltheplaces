from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.user_agents import BROWSER_DEFAULT


class WilliamsSonomaUSSpider(JSONBlobSpider):
    name = "williams_sonoma_us"
    allowed_domains = ["www.williams-sonoma.com"]
    start_urls = [
        "https://www.williams-sonoma.com/search/stores.json?brands=WS,PB&lat=40.71304703&lng=-74.00723267&radius=100000&includeOutlets=false",
    ]
    brands = {
        "WS": {"brand": "Williams-Sonoma", "brand_wikidata": "Q2581220"},
        "PB": {"brand": "Pottery Barn", "brand_wikidata": "Q3400126"},
    }
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    locations_key = ["storeListResponse", "stores"]

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("properties"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item.update(self.brands[feature["BRAND"]])
        item["street_address"] = feature["ADDRESS_LINE_1"]
        item["phone"] = feature["PHONE_NUMBER_FORMATTED"]
        slug = "{}-{}-{}-{}".format(
            feature["COUNTRY_CODE"].lower(),
            feature["STATE_PROVINCE"].lower(),
            feature["CITY"].lower().replace(" ", "-"),
            feature["STORE_NAME"].lower().replace(" ", "-"),
        )
        if feature["BRAND"] == "WS":
            apply_category(Categories.SHOP_HOUSEWARE, item)
            item["website"] = f"https://www.williams-sonoma.com/stores/{slug}/"
        elif feature["BRAND"] == "PB":
            apply_category(Categories.SHOP_FURNITURE, item)
            item["website"] = f"https://www.potterybarn.com/stores/{slug}/"
        item["opening_hours"] = OpeningHours()
        for day_name in DAYS_FULL:
            day_hours = feature.get("{}_HOURS_FORMATTED".format(day_name.upper()))
            if not day_hours:
                continue
            item["opening_hours"].add_range(day_name, *day_hours.split(" - ", 1), "%I:%M %p")
        yield item
