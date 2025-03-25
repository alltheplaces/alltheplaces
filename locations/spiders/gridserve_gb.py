from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class GridserveGBSpider(Spider):
    name = "gridserve_gb"
    item_attributes = {"operator": "Gridserve", "operator_wikidata": "Q89575318"}
    start_urls = ["https://gfxpushnode.gridserve.com/api/v1/charging-station-by-locations"]

    def parse(self, response, **kwargs):
        for location in response.json()["data"]:
            if location["type_status"] != "live":
                continue

            item = DictParser.parse(location)

            item["extras"]["check_date"] = location["updatedAt"]

            # TODO: connector data location["connectors"]

            apply_category(Categories.CHARGING_STATION, item)
            yield item
