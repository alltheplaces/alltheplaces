from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class LasVegasCityCouncilTreesUSSpider(ArcGISFeatureServerSpider):
    name = "las_vegas_city_council_trees_us"
    item_attributes = {
        "operator": "Las Vegas City Council",
        "operator_wikidata": "Q105801990",
        "state": "NV",
        "nsi_id": "N/A",
    }
    host = "services1.arcgis.com"
    context_path = "F1v0ufATbBQScMtY/ArcGIS"
    service_id = "Trees_PRD"
    layer_id = "10"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["UNIQUEID"])
        item.pop("addr_full", None)
        if feature["STREET"].upper() == "Unassigned":
            item.pop("street", None)
        apply_category(Categories.NATURAL_TREE, item)
        item["extras"]["protected"] = "yes"
        if taxon := feature.get("SPP_BOT"):
            item["extras"]["species"] = taxon
        if common_name := feature.get("SPP_COM"):
            item["extras"]["taxon:en"] = common_name
        if height_range_ft := feature.get("HEIGHT").strip():
            if height_range_ft != "---" and height_range_ft != "0":
                if height_range_ft.startswith(">"):
                    min_height_ft = height_range_ft.removeprefix(">").strip()
                    item["extras"]["height"] = f"{min_height_ft} '"
                else:
                    min_height_ft, max_height_ft = height_range_ft.split("-", 1)
                    item["extras"]["height:range"] = f"{min_height_ft} - {max_height_ft}'"
        if dbh_range_ft := feature.get("DBH").strip():
            if dbh_range_ft != "---" and dbh_range_ft != "0":
                if dbh_range_ft.startswith(">"):
                    min_dbh_ft = dbh_range_ft.removeprefix(">").strip()
                    item["extras"]["diameter"] = f"{min_dbh_ft} '"
                else:
                    min_dbh_ft, max_dbh_ft = dbh_range_ft.split("-", 1)
                    item["extras"]["diameter:range"] = f"{min_dbh_ft} - {max_dbh_ft}'"
        yield item
