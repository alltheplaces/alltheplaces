from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.storefinders.algolia import AlgoliaSpider


class OrangePLSpider(AlgoliaSpider):
    name = "orange_pl"
    item_attributes = {"brand": "Orange", "brand_wikidata": "Q1431486", "extras": Categories.SHOP_MOBILE_PHONE.value}
    api_key = "7a46160ed01bb0af2c2af8d14b97f3c5"
    app_id = "0KNEMTBXX3"
    index_name = "OEPL_en"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street_address"] = clean_address([feature.pop("street1"), feature.pop("street2")])
        item["addr_full"] = clean_address(feature["formatted_address"])
        item["lat"] = feature["_geoloc"]["lat"]
        item["lon"] = feature["_geoloc"]["lng"]
        item["country"] = feature["country"]["code"]
        item["city"] = feature["city"]["name"]
        item["website"] = f"https://salony.orange.pl/pl/{feature['url_location']}"
        item.pop("name", None)
        item["opening_hours"] = self.extract_opening_hours(feature)
        yield item

    def extract_opening_hours(self, feature: dict) -> OpeningHours:
        if hours := feature.get("formatted_opening_hours"):
            try:
                oh = OpeningHours()
                for day, hour in hours.items():
                    for times in hour:
                        oh.add_range(day, times.split("-")[0], times.split("-")[1], time_format="%I:%M%p")
                return oh
            except Exception as e:
                self.logger.warning(f"Failed to parse hours {hours}: {e}")
