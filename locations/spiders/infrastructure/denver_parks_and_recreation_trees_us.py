from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class DenverParksAndRecreationTreesUSSpider(ArcGISFeatureServerSpider):
    name = "denver_parks_and_recreation_trees_us"
    item_attributes = {"operator": "Denver Parks and Recreation", "operator_wikidata": "Q133829945", "state": "CO"}
    host = "services1.arcgis.com"
    context_path = "zdB7qR0BtYrg0Xpl/ArcGIS"
    service_id = "ODC_PARK_TREEINVENTORY_P"
    layer_id = "241"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("SPECIES_BOTANIC") in (
            "Vacant Site",
            "_Vacant",
            "_Vacant site-not plantable",
            "Stump",
            "_Stump",
        ):
            return
        item["ref"] = feature["GlobalID"]
        item.pop("name", None)
        item.pop("addr_full", None)
        item.pop("street", None)
        item["housenumber"] = feature.get("ADDRESS")
        item["street_address"] = feature.get("STREET")
        apply_category(Categories.NATURAL_TREE, item)
        item["extras"]["protected"] = "yes"
        item["extras"]["species"] = feature.get("SPECIES_BOTANIC")
        item["extras"]["taxon:en"] = feature.get("SPECIES_COMMON")
        if dbh_range_in := feature.get("DIAMETER"):
            if " to " in dbh_range_in:
                dbh_low_in, dbh_high_in = dbh_range_in.split(" to ", 1)
                item["extras"]["diameter:range"] = f'{dbh_low_in} - {dbh_high_in}"'
            elif dbh_range_in.endswith("+"):
                dbh_min_in = dbh_range_in.removesuffix("+").strip()
                item["extras"]["diameter"] = f'{dbh_min_in}"'
            elif dbh_range_in.isnumeric():
                item["extras"]["diameter"] = f'{dbh_range_in}"'
        yield item
