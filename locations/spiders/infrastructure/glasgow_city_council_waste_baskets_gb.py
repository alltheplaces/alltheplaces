from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class GlasgowCityCouncilWasteBasketsGBSpider(ArcGISFeatureServerSpider):
    name = "glasgow_city_council_waste_baskets_gb"
    item_attributes = {
        "operator": "Glasgow City Council",
        "operator_wikidata": "Q130637",
        "nsi_id": "N/A",
    }
    host = "utility.arcgis.com"
    context_path = "usrsvcs/servers/673f7e72d70947eaa50187da15f41469"
    service_id = "AGOL/FeatureAccess_Litter_Bin_Locations"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["id"])
        apply_category(Categories.WASTE_BASKET, item)
        if volume_l := feature.get("CAPACITY"):
            # "volume" is a made-up key that doesn't currently exist in OSM.
            # No other existing key for the volume of a bin appears to
            # currently exist in OSM.
            item["extras"]["volume"] = f"{volume_l}"
        yield item
