from datetime import UTC, datetime
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class LauncestonCityCouncilTreesAUSpider(ArcGISFeatureServerSpider):
    name = "launceston_city_council_trees_au"
    item_attributes = {"operator": "Launceston City Council", "operator_wikidata": "Q132860984"}
    host = "mapping.launceston.tas.gov.au"
    context_path = "arcgis"
    service_id = "Public/ParksAndRecreation"
    layer_id = "1"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["gisassetid"])
        apply_category(Categories.NATURAL_TREE, item)
        if species := feature.get("genusspecies"):
            species = species.strip()
            if species:
                item["extras"]["species"] = species
        if taxon_en := item.pop("name", None):
            taxon_en = taxon_en.strip()
            if taxon_en:
                item["extras"]["taxon:en"] = taxon_en
        item["extras"]["protected"] = "yes"
        if planted_unix_timestamp := feature.get("planteddate"):
            planted_date = datetime.fromtimestamp(int(float(planted_unix_timestamp) / 1000), UTC)
            item["extras"]["start_date"] = planted_date.strftime("%Y-%m-%d")
        yield item
