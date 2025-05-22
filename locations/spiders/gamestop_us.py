import re
from json import loads

from scrapy import Spider
from scrapy.http import Request

from locations.categories import Categories, apply_category
from locations.geo import country_iseadgg_centroids
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS

GAMESTOP_SHARED_ATTRIBUTES = {
    "brand": "GameStop",
    "brand_wikidata": "Q202210",
}


class GamestopUSSpider(Spider):
    name = "gamestop_us"
    item_attributes = GAMESTOP_SHARED_ATTRIBUTES
    allowed_domains = ["www.gamestop.com"]
    start_urls = [
        "https://www.gamestop.com/on/demandware.store/Sites-gamestop-us-Site/default/Stores-FindStores?radius=900"
    ]
    is_playwright_spider = True
    custom_settings = {"ROBOTSTXT_OBEY": False} | DEFAULT_PLAYWRIGHT_SETTINGS
    requires_proxy = True  # Data centre IP ranges appear to be blocked.

    def start_requests(self):
        for coordinates in country_iseadgg_centroids(["US"], 458):
            yield Request(url=f"{self.start_urls[0]}&lat={coordinates[0]}&long={coordinates[1]}")

    def parse(self, response):
        json_blob = loads(response.xpath("//pre/text()").get())
        for store in json_blob["stores"]:
            store_name_clean = re.sub(r"- GameStop", "", store["name"].strip(), flags=re.IGNORECASE)
            properties = {
                "ref": store["ID"],
                "branch": store_name_clean,
                "lat": store["latitude"],
                "lon": store["longitude"],
                "street_address": re.sub(
                    r"\bSTE ",
                    "Suite ",
                    merge_address_lines([store["address2"], store["address1"]]),
                    flags=re.IGNORECASE,
                ),
                "city": store["city"],
                "postcode": store["postalCode"],
                "state": store["stateCode"],
                "phone": store["phone"],
                "website": "https://www.gamestop.com/store/us/{}/{}/{}/{}-gamestop".format(
                    store["stateCode"].lower(),
                    store["city"].lower().replace(" ", "-"),
                    store["ID"],
                    store_name_clean.lower().replace(" ", "-"),
                ),
                "opening_hours": OpeningHours(),
            }
            for day_hours in loads(store["storeOperationHours"]):
                properties["opening_hours"].add_range(
                    DAYS_EN[day_hours["day"]], day_hours["open"], day_hours["close"], "%H%M"
                )
            apply_category(Categories.SHOP_VIDEO_GAMES, properties)
            yield Feature(**properties)
