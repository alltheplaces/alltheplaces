from datetime import UTC, datetime
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class BendCityCouncilFireHydrantsUSSpider(ArcGISFeatureServerSpider):
    name = "bend_city_council_fire_hydrants_us"
    item_attributes = {"operator": "Bend City Council", "operator_wikidata": "Q134540047", "state": "OR"}
    host = "services5.arcgis.com"
    context_path = "JisFYcK2mIVg9ueP/ArcGIS"
    service_id = "Hydrant"
    layer_id = "5"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["assetid"]
        item.pop("name", None)
        apply_category(Categories.FIRE_HYDRANT, item)
        if pressure_psi := feature.get("pressure"):
            item["extras"]["fire_hydrant:pressure"] = f"{pressure_psi} psi"
        if diameter_1_in := feature.get("diameter"):
            if diameter_2_in := feature.get("secondarydiameter"):
                item["extras"]["fire_hydrant:diameter"] = f'{diameter_1_in}";{diameter_2_in}"'
            else:
                item["extras"]["fire_hydrant:diameter"] = f'{diameter_1_in}"'
        if install_date_int := feature.get("installdate"):
            install_date = datetime.fromtimestamp(int(float(install_date_int) / 1000), UTC)
            item["extras"]["start_date"] = install_date.isoformat().split("T", 1)[0]
        yield item
