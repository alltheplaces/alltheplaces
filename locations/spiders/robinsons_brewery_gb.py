from typing import Any

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider

FACILITIES = {
    "facility_beer_garden": Extras.OUTDOOR_SEATING,
    "facility_dog_friendly": Extras.DOG,
    "facility_wheelchair_accessible": Extras.WHEELCHAIR,
    "facility_wifi": Extras.WIFI,
}


class RobinsonsBreweryGBSpider(JSONBlobSpider):
    name = "robinsons_brewery_gb"
    item_attributes = {
        "brand": "Robinsons",
        "brand_wikidata": "Q7353116",
    }
    start_urls = ["https://www.robinsonsbrewery.com/wp-json/robinsons/v1/pub-search?lat=53.4&lng=-2.1&radius=1000"]
    locations_key = "results"

    def pre_process_data(self, feature: dict) -> None:
        feature["ref"] = feature.pop("pub_id")
        feature["street_address"] = feature.pop("address_1")

    def post_process_item(self, item: Feature, response: Response, feature: dict, **kwargs: Any) -> Any:
        apply_category(Categories.PUB, item)
        for key, attribute in FACILITIES.items():
            apply_yes_no(attribute, item, feature.get(key) == "1")
        yield JsonRequest(
            url="https://www.robinsonsbrewery.com/wp-json/brew/v1/pub-opening-times/{}".format(item["ref"]),
            callback=self.parse_opening_hours,
            cb_kwargs={"item": item},
        )

    def parse_opening_hours(self, response: Response, item: Feature, **kwargs: Any) -> Any:
        item["opening_hours"] = OpeningHours()
        if isinstance(opening := response.json().get("opening"), dict):
            for day, ranges in opening.items():
                if ranges is False:
                    item["opening_hours"].set_closed(day)
                    continue
                for time_range in ranges:
                    item["opening_hours"].add_range(day, time_range["open"], time_range["close"])
        yield item
