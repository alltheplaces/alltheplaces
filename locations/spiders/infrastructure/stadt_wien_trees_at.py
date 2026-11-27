from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.licenses import Licenses


class StadtWienTreesATSpider(JSONBlobSpider):
    name = "stadt_wien_trees_at"
    item_attributes = {"operator": "Stadt Wien", "operator_wikidata": "Q1741", "nsi_id": "N/A"}
    dataset_attributes = Licenses.CCBY4.value | {"attribution:name": "Stadt Wien – data.wien.gv.at"}
    allowed_domains = ["data.wien.gv.at"]
    start_urls = [
        "https://data.wien.gv.at/daten/geo?service=WFS&request=GetFeature&version=1.1.0&typeName=ogdwien:BAUMKATOGD&srsName=EPSG:4326&outputFormat=json"
    ]
    locations_key = "features"
    custom_settings = {"DOWNLOAD_TIMEOUT": 300}

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("properties"))

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        # Planned planting spots without a tree yet
        if feature["GATTUNG_ART"] == "Jungbaum wird gepflanzt":
            return
        item["ref"] = str(feature["BAUM_ID"])
        apply_category(Categories.NATURAL_TREE, item)
        if " (" in feature["GATTUNG_ART"]:
            species, taxon_de = feature["GATTUNG_ART"].removesuffix(")").split(" (")
            if species.endswith(" spec."):
                item["extras"]["genus"] = species.removesuffix(" spec.")
            else:
                item["extras"]["species"] = species
            item["extras"]["taxon:de"] = taxon_de
        if feature["PFLANZJAHR"]:
            item["extras"]["start_date"] = str(feature["PFLANZJAHR"])
        if feature["STAMMUMFANG"]:
            item["extras"]["circumference"] = f"{feature['STAMMUMFANG']} cm"
        yield item
