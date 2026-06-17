from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Clothes, apply_category, apply_clothes
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class ZaraSpider(JSONBlobSpider):
    name = "zara"
    item_attributes = {"brand": "Zara", "brand_wikidata": "Q147662"}
    countries = [
        ("at", 47.59397, 14.12456),
        ("be", 50.6402809, 4.6667145),
        ("bg", 42.6073975, 25.4856617),
        ("br", -10.3333333, -53.2),
        ("ca", 61.0666922, -107.991707),
        ("ch", 46.7985624, 8.2319736),
        ("co", 4.099917, -72.9088133),
        ("cr", 10.2735633, -84.0739102),
        ("cz", 49.7439047, 15.3381061),
        ("de", 51.1638175, 10.4478313),
        ("ee", 58.7523778, 25.3319078),
        # Search seems to be limited to 100 results, so ES and FR need several starting points to find all stores
        ("es", 37.8845813, -4.7760138),
        ("es", 41.6521342, -0.8809428),
        ("es", 28.4671780, -16.2507843),
        ("fr", 48.8534951, 2.3483915),
        ("fr", 45.5504338, 3.7426390),
        ("gr", 38.9953683, 21.9877132),
        ("hr", 45.3658443, 15.6575209),
        ("hu", 47.1817585, 19.5060937),
        ("id", -2.4833826, 117.8902853),
        ("ie", 52.865196, -7.9794599),
        ("il", 30.8124247, 34.8594762),
        ("in", 22.3511148, 78.6677428),
        ("it", 42.6384261, 12.674297),
        ("jp", 36.5748441, 139.2394179),
        ("kr", 36.638392, 127.6961188),
        ("lt", 55.3500003, 23.7499997),
        ("lv", 56.8406494, 24.7537645),
        ("ma", 31.1728205, -7.3362482),
        ("mx", 23.6585116, -102.0077097),
        ("nl", 52.2434979, 5.6343227),
        ("pe", -6.8699697, -75.0458515),
        ("ph", 12.7503486, 122.7312101),
        ("pl", 52.215933, 19.134422),
        ("pt", 39.6621648, -8.1353519),
        ("ro", 45.9852129, 24.6859225),
        ("rs", 44.1534121, 20.55144),
        ("sg", 1.357107, 103.8194992),
        ("si", 46.1199444, 14.8153333),
        ("sk", 48.7411522, 19.4528646),
        ("tr", 39.294076, 35.2316631),
        ("uk", 54.7023545, -3.2765753),
        ("us", 39.7837304, -100.445882),
    ]
    start_urls = [
        f"https://www.zara.com/{country}/en/stores-locator/extended/search?lat={lat}&lng={lng}&isDonationOnly=false&showOnlyPickup=false&showStoresCapacity=false&radius=1000&ajax=true"
        for country, lat, lng in countries
    ]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:150.0) Gecko/20100101 Firefox/150.0",
        "DEFAULT_REQUEST_HEADERS": {
            "Host": "www.zara.com",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Connection": "keep-alive",
            "Referer": "https://www.zara.com/uk/en/z-stores-st1404.html?v1=2418845",
        },
    }

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
        if feature["phones"]:
            item["phone"] = feature["phones"][0]
        if "commercialName" in feature:
            item["branch"] = feature["commercialName"].removeprefix("ZARA ")
        item["opening_hours"] = OpeningHours()
        for day in feature["openingHours"]:
            for interval in day["openingHoursInterval"]:
                item["opening_hours"].add_range(DAYS[day["weekDay"] - 1], interval["openTime"], interval["closeTime"])
        yield item
