from datetime import UTC, datetime
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class AuroraCityCouncilTreesUSSpider(ArcGISFeatureServerSpider):
    name = "aurora_city_council_trees_us"
    item_attributes = {"operator": "Aurora City Council", "operator_wikidata": "Q138498688", "state": "CO"}
    host = "services3.arcgis.com"
    context_path = "0Va1ID99NSrNyyPX/arcgis"
    service_id = "Trees_public_d2e03763c35b47d1875d2b413c76fbda"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("spacestatus") != "Planted":
            return

        item["ref"] = feature["assetid"]
        item["street_address"] = feature.get("fulladdr")

        apply_category(Categories.NATURAL_TREE, item)

        genus = feature.get("genus")
        if genus:
            genus = genus.strip()
            item["extras"]["genus"] = genus
        else:
            genus = ""
        species = feature.get("species")
        if species:
            species = species.strip()
        else:
            species = ""
        cultivar = feature.get("cultivar")
        if cultivar:
            cultivar = cultivar.strip()
        else:
            cultivar = ""
        if genus and (species or cultivar):
            item["extras"]["species"] = "{} {} {}".format(genus, species, cultivar).strip()
        item["extras"]["taxon:en"] = feature.get("commonname")

        if dbh_in := feature.get("diameter"):
            item["extras"]["diameter"] = f'{dbh_in}"'

        if planted_unix_timestamp := feature.get("installdate"):
            planted_date = datetime.fromtimestamp(int(float(planted_unix_timestamp) / 1000), UTC)
            item["extras"]["start_date"] = planted_date.strftime("%Y-%m-%d")

        yield item
