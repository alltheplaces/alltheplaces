from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours, DAYS
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class CityOfMelbourneToiletsAUSpider(JSONBlobSpider):
    name = "city_of_melbourne_toilets_au"
    item_attributes = {"operator": "City of Melbourne", "operator_wikidata": "Q1919098"}
    allowed_domains = ["maps.melbourne.vic.gov.au"]
    start_urls = ["https://maps.melbourne.vic.gov.au/weave/services/v1/feature/getFeatures?shape=POLYGON((278984.5214999998%205773194.2749,278984.5214999998%205853194.1042,361023.5938999998%205853194.1042,361023.5938999998%205773194.2749,278984.5214999998%205773194.2749))&entityId=lyr_publictoilet&datadefinition=__dd__ar_public_toilet&outCrs=EPSG:4326&inCrs=EPSG:7855&operation=intersects&returnCentroid=true&returnFirst=false"]
    locations_key = "features"

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature["properties"]["__dd__ar_public_toilet"][0])

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["np_assetid"])
        item["addr_full"] = feature["st_description"]

        apply_category(Categories.TOILETS, item)
        apply_category({"access": "yes"}, item)
        apply_category({"fee": "no"}, item)
        if feature["st_accessible"] and feature["st_accessible"] in ["Yes", "No"]:
            apply_yes_no(Extras.WHEELCHAIR, item, feature["st_accessible"] == "Yes", False)
        if feature["st_baby"] and feature["st_baby"] in ["Yes", "No"]:
            apply_yes_no(Extras.BABY_CHANGING_TABLE, item, feature["st_baby"] == "Yes", False)
        if feature["st_unisex"] and feature["st_unisex"] in ["Yes", "No"]:
            apply_yes_no(Extras.UNISEX, item, feature["st_unisex"] == "Yes", False)
        if feature["st_female"] and feature["st_female"] in ["Yes", "No"]:
            apply_yes_no(Extras.FEMALE, item, feature["st_female"] == "Yes", False)
        if feature["st_male"] and feature["st_male"] in ["Yes", "No"]:
            apply_yes_no(Extras.MALE, item, feature["st_male"] == "Yes", False)

        item["opening_hours"] = OpeningHours()
        if feature["st_open"] is None or feature["st_closed"] is None:
            item["opening_hours"].add_days_range(DAYS, "00:00", "23:59")
        elif feature["st_open"] == "00:00" and feature["st_open"] == "00:00":
            item["opening_hours"].add_days_range(DAYS, "00:00", "23:59")
        else:
            item["opening_hours"].add_days_range(DAYS, feature["st_open"], feature["st_closed"])

        yield item
