from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.socrata import SocrataSpider


class SanFranciscoDepartmentOfPublicWorksTreesUSSpider(SocrataSpider):
    name = "san_francisco_department_of_public_works_trees_us"
    item_attributes = {"state": "CA", "nsi_id": "N/A"}
    host = "data.sfgov.org"
    resource_id = "tkzw-k3nq"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("planttype") not in ["Tree", "tree"] or feature.get("qlegalstatus") == "Permitted Site":
            return
        item["ref"] = feature["treeid"]
        item["street_address"] = feature.get("qaddress")
        apply_category(Categories.NATURAL_TREE, item)
        item["extras"]["protected"] = "yes"
        if species_name := feature.get("qspecies"):
            if species_name not in ["Tree(s) ::"] and " :: " in species_name:
                item["extras"]["species"] = species_name.split(" :: ", 1)[0]
                item["extras"]["taxon:en"] = species_name.split(" :: ", 1)[1]
        if location_type := feature.get("qsiteinfo"):
            if location_type.startswith("Sidewalk:"):
                item["operator"] = "San Francisco Department of Public Works"
                item["operator_wikidata"] = "Q7413995"
        if dbh_in := feature.get("dbh"):
            item["extras"]["diameter"] = f"{dbh_in}\""
        yield item
