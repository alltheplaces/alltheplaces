from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.opendatasoft_explore import OpendatasoftExploreSpider


class GreaterGeelongCityCouncilTreesAUSpider(OpendatasoftExploreSpider):
    name = "greater_geelong_city_council_trees_au"
    item_attributes = {"operator": "Greater Geelong City Council", "operator_wikidata": "Q112919122", "nsi_id": "N/A"}
    api_endpoint = "https://www.geelongdataexchange.com.au/api/explore/v2.1/"
    dataset_id = "plaprodplacestreepoints_prod"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["tree_id"])
        item["street_address"] = item.pop("addr_full", None)
        item["state"] = "VIC"
        apply_category(Categories.NATURAL_TREE, item)
        item["extras"]["species"] = " ".join(list(filter(None, [feature["genus"], feature["species"]])))
        item["extras"]["genus"] = feature["genus"]
        item["extras"]["taxon:en"] = feature["common"]
        item["extras"]["protected"] = "yes"
        if dbh_range_cm := feature.get("dbh"):
            item["extras"]["diameter:range"] = f"{dbh_range_cm} m"
        if height_m := feature.get("height"):
            item["extras"]["height"] = f"{height_m} m"
        elif height_range_m := feature.get("height_range"):
            height_range_m = height_range_m.lower().removesuffix("metres").strip()
            item["extras"]["height:range"] = f"{height_range_m} m"
        if crown_width_m := feature.get("crown_width"):
            item["extras"]["diameter_crown"] = f"{crown_width_m} m"
        if planting_year := feature.get("plant_year"):
            item["extras"]["start_date"] = str(planting_year)
        yield item
