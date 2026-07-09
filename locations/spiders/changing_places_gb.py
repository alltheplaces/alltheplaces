from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class ChangingPlacesGBSpider(JSONBlobSpider):
    name = "changing_places_gb"
    item_attributes = {"brand": "Changing Places", "brand_wikidata": "Q104870811"}
    start_urls = ["https://www.changing-places.org/api/getToilets"]
    locations_key = "toilets"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["lat"] = feature.get("la")
        item["lon"] = feature.get("lo")
        item["name"] = "Changing Places"
        item["branch"] = feature.get("n")
        item["street_address"] = ", ".join(filter(None, (feature.get("a1"), feature.get("a2"))))
        item["city"] = feature.get("c")
        item["postcode"] = feature.get("p")
        item["website"] = "https://www.changing-places.org/find?toilet=" + str(item["ref"])
        item["extras"]["location_type"] = feature.get("bt")
        item["opening_hours"] = OpeningHours()
        for i in range(6):
            if feature["ds"] == 1:
                item["opening_hours"].add_range(DAYS[i], "00:00", "24:00")
            elif feature["ds"] == 2:
                item["opening_hours"].set_closed(DAYS[i])
            else:
                item["opening_hours"].add_range(DAYS[i], feature["do"][i], feature["dc"][i])

        apply_category(Categories.TOILETS, item)

        yield item
