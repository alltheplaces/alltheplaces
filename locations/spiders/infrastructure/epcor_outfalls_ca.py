from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.socrata import SocrataSpider


class EpcorOutfallsCASpider(SocrataSpider):
    name = "epcor_outfalls_ca"
    item_attributes = {"operator": "EPCOR", "operator_wikidata": "Q5323849", "state": "AB"}
    host = "data.edmonton.ca"
    resource_id = "gpxt-s37s"
    no_refs = True

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street_address"] = feature.get("road_name")
        item["city"] = feature.get("neighbourhood_name")
        apply_category(Categories.MANHOLE, item)
        if feature.get("type") == "STORM":
            item["extras"]["utility"] = "stormwater"
            item["extras"]["substance"] = "rainwater"
        elif feature.get("type") == "SANITARY":
            item["extras"]["utility"] = "sewerage"
            item["extras"]["substance"] = "sewage"
        elif feature.get("type") == "COMBINED":
            item["extras"]["utility"] = "sewerage"
            item["extras"]["substance"] = "rainwater;sewage"
        else:
            self.logger.warning("Unknown utility type: {}".format(feature["type"]))
        if construction_year := feature.get("year_const"):
            if construction_year != "9999":
                item["extras"]["start_date"] = construction_year
        yield item
