import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class NiagaraFallsCityCouncilGravesCASpider(ArcGISFeatureServerSpider):
    name = "niagara_falls_city_council_graves_ca"
    item_attributes = {"operator": "Niagara Falls City Council", "operator_wikidata": "Q16941501", "state": "ON"}
    host = "services9.arcgis.com"
    context_path = "oMFQlUUrLd1Uh1bd/ArcGIS"
    service_id = "Niagara_Falls_Cemetery_Plots"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = "_".join(
            filter(
                None,
                [
                    feature.get("Cemetery"),
                    feature.get("CemSection"),
                    feature.get("CemRow"),
                    feature.get("CemLot"),
                    feature.get("CemSubLot"),
                ],
            )
        )
        name = ""
        if feature.get("FirstNames") and feature.get("FirstNames") != "UNKNOWN":
            name = feature["FirstNames"]
        if feature.get("LastName") and feature.get("LastName") != "UNKNOWN":
            name = " ".join([name, feature["LastName"]])
        if name:
            item["name"] = name
        if image := feature.get("Image_url"):
            item["image"] = image
        apply_category(Categories.GRAVE, item)
        if m := re.fullmatch(r"^(\d{2})\/(\d{2})\/(\d{4})$", feature.get("Date_inter")):
            item["extras"]["start_date"] = "{}-{}-{}".format(m.group(3), m.group(1), m.group(2))
        yield item
