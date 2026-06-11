import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class BoroondaraCityCouncilReservesAUSpider(JSONBlobSpider):
    name = "boroondara_city_council_reserves_au"
    item_attributes = {"operator": "Boroondara City Council", "operator_wikidata": "Q56477791", "state": "VIC"}
    allowed_domains = ["www.boroondara.vic.gov.au"]
    start_urls = ["https://www.boroondara.vic.gov.au/rest/locations?tid[]=781&tid[]=801&tid[]=806&tid[]=1401"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["nid"])
        item["name"] = (
            feature["title"]
            .removeprefix("Barbecue - ")
            .removeprefix("Playground - ")
            .removeprefix("Playround - ")
            .removeprefix("Picnic Shelter - ")
            .removeprefix("Rotunda - ")
            .strip()
        )
        item["addr_full"] = re.sub(r"\s+", " ", feature["field_location"]).strip()
        item["lat"], item["lon"] = re.sub(r"\s+", "", feature["field_geo_information"]).strip().split(",", 1)
        match feature["field_location_category"][0]:
            case "781":
                apply_category(Categories.BARBECUE, item)
            case "801":
                apply_category(Categories.LEISURE_PARK, item)
            case "806":
                apply_category(Categories.LEISURE_PICNIC_SHELTER, item)
            case "1401":
                apply_category(Categories.LEISURE_GAZEBO, item)
            case _:
                self.logger.warning(
                    "Unknown feature type '{}'. Feature has unique ID of '{}' and title of '{}'.".format(
                        feature["field_location_category"][0], feature["nid"], feature["title"]
                    )
                )
        yield item
