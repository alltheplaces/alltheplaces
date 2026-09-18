from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class HeinensUSSpider(Spider):
    name = "heinens_us"
    item_attributes = {"name": "Heinen's", "brand_wikidata": "Q5699702"}
    allowed_domains = ["www.heinens.com"]
    start_urls = ["https://www.heinens.com/wp-json/wp/v2/store?per_page=100"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():
            location = store["map"]

            item = Feature()
            item["ref"] = store["heinens_id"]
            item["branch"] = store["title"]["rendered"]
            item["website"] = store["link"]
            item["phone"] = store["phone_number"]
            item["lat"] = location.get("lat")
            item["lon"] = location.get("lng")
            item["housenumber"] = location.get("street_number")
            item["street"] = location.get("street_name_short")
            item["city"] = location.get("city")
            item["state"] = location.get("state_short")
            item["postcode"] = location.get("post_code")
            item["country"] = location.get("country_short")
            if place_id := location.get("place_id"):
                item["extras"]["ref:google:place_id"] = place_id

            item["opening_hours"] = OpeningHours()
            for rule in store.get("hours") or []:
                days = [DAYS[int(day) - 1] for day in rule["days"]]
                item["opening_hours"].add_days_range(days, rule["opens"], rule["closes"], time_format="%I:%M %p")

            apply_category(Categories.SHOP_SUPERMARKET, item)

            yield item
