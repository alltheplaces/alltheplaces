from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.vector_file_spider import VectorFileSpider


class GreaterBendigoCityCouncilDisabledParkingSpacesAUSpider(VectorFileSpider):
    name = "greater_bendigo_city_council_disabled_parking_spaces_au"
    item_attributes = {"operator": "Greater Bendigo City Council", "operator_wikidata": "Q134285890", "state": "VIC"}
    allowed_domains = ["connect.pozi.com"]
    start_urls = ["https://connect.pozi.com/userdata/bendigo-publisher/Pozi_Public_City_of_Greater_Bendigo/Accessible_Parking.fgb"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if not feature["Responsibility"].startswith("CoGB "):
            # Private car space not operated by CoGB.
            return
        item["ref"] = str(feature["id"])
        apply_category(Categories.PARKING_SPACE, item)
        item["extras"]["parking_space"] = "disabled"
        item["extras"]["alt_ref"] = feature["Reference ID"]
        match feature["Time Restrictions"]:
            case "All Day" | "None":
                item["extras"]["max_stay"] = "no"
            case "1/4 P":
                item["extras"]["max_stay"] = "15 minutes"
            case "1/2 P":
                item["extras"]["max_stay"] = "30 minutes"
            case "1 P":
                item["extras"]["max_stay"] = "1 hour"
            case "1 1/2 P":
                item["extras"]["max_stay"] = "1.5 hours"
            case "2 P":
                item["extras"]["max_stay"] = "2 hours"
            case "3 P":
                item["extras"]["max_stay"] = "3 hours"
            case "4 P":
                item["extras"]["max_stay"] = "4 hours"
            case "Unknown":
                pass
            case _:
                self.logger.warning("Unparsed parking space time restriction: {}".format(feature["Time Restrictions"]))
        yield item
