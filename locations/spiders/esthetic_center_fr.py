from typing import Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class EstheticCenterFRSpider(JSONBlobSpider):
    name = "esthetic_center_fr"
    item_attributes = {"brand": "Esthetic Center", "brand_wikidata": "Q123321775"}
    start_urls = ["https://www.esthetic-center.com/wp-json/wp/v2/institut?per_page=100"]

    def parse(self, response: Response) -> Iterable[Feature | JsonRequest]:
        features = [{**feature.pop("acf"), **feature} for feature in response.json()]
        yield from self.parse_feature_array(response, features)
        if response.meta.get("page") is None:
            for page in range(2, int(response.headers["X-WP-TotalPages"]) + 1):
                yield JsonRequest(f"{self.start_urls[0]}&page={page}", meta={"page": page})

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item.pop("name")
        item["ref"] = feature["slug"]
        item["website"] = feature["link"]
        item["branch"] = feature["titre"].removeprefix("Esthetic Center ")
        item["addr_full"] = feature["adresse"]

        item["opening_hours"] = OpeningHours()
        for day_hours in feature["horaires"].split("|"):
            day, hours = day_hours.split("=")
            if hours == "0":
                item["opening_hours"].set_closed(day)
            else:
                item["opening_hours"].add_range(day, *hours.split(" - "))

        apply_category(Categories.SHOP_BEAUTY, item)
        yield item
