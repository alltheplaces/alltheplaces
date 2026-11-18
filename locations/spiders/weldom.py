import re
from collections import Counter
from datetime import datetime
from typing import Iterable
from urllib.parse import quote
from zoneinfo import ZoneInfo

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines

QUERY = """{storeList(currentPage:1,pageSize:1000){items{
id name url_key is_active timezone contact_phone photos
address{street city postcode latitude longitude}
opening_hours{day_of_week slots{start_time end_time}}
social_networks{type url}}}}"""

TIMEZONE_COUNTRIES = {
    "Europe/Paris": "FR",
    "Indian/Reunion": "RE",
    "America/Guadeloupe": "GP",
    "America/Cayenne": "GF",
    "America/Marigot": "MF",
}


class WeldomSpider(JSONBlobSpider):
    name = "weldom"
    # NSI's "fr" entry doesn't match overseas items in ATP, so name and category are set here.
    item_attributes = {"brand": "Weldom", "brand_wikidata": "Q16683226", "name": "Weldom"}
    start_urls = ["https://www.weldom.fr/graphql?query=" + quote(QUERY)]
    locations_key = ["data", "storeList", "items"]
    # DataDome blocks CI's datacenter IPs, even for a real browser.
    requires_proxy = "FR"
    # DataDome bans the project user agent even through the proxy, so the proxy
    # is left to choose one. robots.txt disallows /graphql.
    custom_settings = {"USER_AGENT": None, "ROBOTSTXT_OBEY": False}

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        stores = [store for store in self.extract_json(response) if store["is_active"]]
        # Brand-wide Facebook pages and photos are listed on several stores.
        self.facebook_counts = Counter(
            s["url"] for store in stores for s in store["social_networks"] if s["type"] == "FACEBOOK"
        )
        self.photo_counts = Counter(photo for store in stores for photo in store["photos"])
        yield from self.parse_feature_array(response, stores)

    def pre_process_data(self, store: dict) -> None:
        store.update(store.pop("address"))
        store["street_address"] = merge_address_lines(store.pop("street"))

    def post_process_item(self, item: Feature, response: TextResponse, store: dict) -> Iterable[Feature]:
        if name := item.pop("name", None):
            item["branch"] = re.sub(r"(?i)^weldom\s+", "", name)
        item["website"] = f"https://www.weldom.fr/m/{store['url_key']}"
        item["country"] = TIMEZONE_COUNTRIES.get(store["timezone"])
        item["facebook"] = next(
            (
                s["url"]
                for s in store["social_networks"]
                if s["type"] == "FACEBOOK" and self.facebook_counts[s["url"]] == 1
            ),
            None,
        )
        item["image"] = next((photo for photo in store["photos"] if self.photo_counts[photo] == 1), None)

        # Slots are UTC datetimes; convert to the store's local time.
        timezone = ZoneInfo(store["timezone"])
        item["opening_hours"] = OpeningHours()
        for day in store["opening_hours"]:
            weekday = DAYS[day["day_of_week"] - 1]
            if not day["slots"]:
                item["opening_hours"].set_closed(weekday)
            for slot in day["slots"]:
                item["opening_hours"].add_range(
                    weekday,
                    datetime.fromisoformat(slot["start_time"]).astimezone(timezone).strftime("%H:%M"),
                    datetime.fromisoformat(slot["end_time"]).astimezone(timezone).strftime("%H:%M"),
                )

        apply_category(Categories.SHOP_DOITYOURSELF, item)
        yield item
