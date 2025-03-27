from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.socrata import SocrataSpider


class NewYorkCityDepartmentOfParksAndRecreationTreesUSSpider(SocrataSpider):
    name = "new_york_city_department_of_parks_and_recreation_trees_us"
    item_attributes = {"operator": "New York City Department of Parks and Recreation", "operator_wikidata": "Q1894232"}
    host = "data.cityofnewyork.us"
    resource_id = "hn5i-inap"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if condition := feature["tpstructure"]:
            match condition:
                case "Full":
                    pass
                case "Retired" | "Shaft" | "Stump" | "Stump - Uprooted":
                    return
                case _:
                    self.logger.warning("Unknown type of tree condition: `{}`. Tree ignored.".format(condition))
                    return
        else:
            return

        item["ref"] = feature["globalid"]
        apply_category(Categories.NATURAL_TREE, item)

        if species_label := feature["genusspecies"]:
            if " - " in feature["genusspecies"]:
                scientific_name, common_name = feature["genusspecies"].split(" - ", 1)
                item["extras"]["species"] = scientific_name
                item["extras"]["taxon:en"] = common_name
            else:
                item["extras"]["taxon:en"] = feature["genusspecies"]

        item["extras"]["protected"] = "yes"
        if dbh_in := feature.get("dbh"):
            item["extras"]["diameter"] = f"{dbh_in} in"
        if planted_date := feature.get("planteddate"):
            item["extras"]["start_date"] = planted_date.split(" ", 1)[0]

        yield item
