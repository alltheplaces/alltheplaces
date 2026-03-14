import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class NiagaraFallsCityCouncilTreesCASpider(ArcGISFeatureServerSpider):
    name = "niagara_falls_city_council_trees_ca"
    item_attributes = {"operator": "Niagara Falls City Council", "operator_wikidata": "Q16941501", "state": "ON"}
    host = "services9.arcgis.com"
    context_path = "oMFQlUUrLd1Uh1bd/ArcGIS"
    service_id = "Niagara_Falls_Trees_Inventory"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.NATURAL_TREE, item)
        item["extras"]["species"] = feature.get("TreeSpecies")
        if dbh_cm := feature.get("DBHTrunk"):
            item["extras"]["diameter"] = f"{dbh_cm} cm"
        if height_range_m := feature.get("HeightRange"):
            if m := re.fullmatch(r"^(\d{2})-(\d{2}) m", height_range_m):
                item["extras"]["height:range"] = "{}-{} m".format(int(m.group(1)), int(m.group(2)))
        yield item
