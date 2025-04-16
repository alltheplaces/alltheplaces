from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.socrata import SocrataSpider


class EpcorPumpingStationsCASpider(SocrataSpider):
    name = "epcor_pumping_stations_ca"
    item_attributes = {"operator": "EPCOR", "operator_wikidata": "Q5323849", "state": "AB"}
    host = "data.edmonton.ca"
    resource_id = "yhez-gf32"
    no_refs = True

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street_address"] = feature.get("road_name")
        item["city"] = feature.get("neighbourhood_name")
        if feature.get("type") == "STORM":
            apply_category(Categories.PUMPING_STATION_WASTEWATER, item)
            item["extras"]["utility"] = "stormwater"
        elif feature.get("type") == "SANITARY":
            apply_category(Categories.PUMPING_STATION_SEWAGE, item)
        elif feature.get("type") == "COMBINED":
            apply_category(Categories.PUMPING_STATION_SEWAGE, item)
            item["extras"]["substance"] = "wastewater;sewage"
        else:
            self.logger.warning("Unknown utility type: {}".format(feature["type"]))
        if construction_year := feature.get("year_const"):
            if construction_year != "9999":
                item["extras"]["start_date"] = construction_year
        yield item
