import re

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class GridserveGBSpider(Spider):
    name = "gridserve_gb"
    item_attributes = {"operator": "Gridserve", "operator_wikidata": "Q89575318"}
    start_urls = ["https://electrichighway.gridserve.com/_next/static/chunks/app/page-0bebb48865ab85ed.js"]

    def parse(self, response, **kwargs):
        token = re.search(r"Q=\"(.*)\";var\s*q", response.text).group(1)
        yield JsonRequest(
            url="https://dnms-api.gridserve.com/api/v1/locations/1/All?searchText=&sort=&orderType=asc",
            headers={"authorization": "Bearer " + token},
            callback=self.parse_locations,
        )

    def parse_locations(self, response):
        for location in response.json()["data"]:
            if location["type_status"] != "live":
                continue

            item = DictParser.parse(location)

            item["extras"]["check_date"] = location["updatedAt"]

            # TODO: connector data location["connectors"]

            apply_category(Categories.CHARGING_STATION, item)
            yield item
