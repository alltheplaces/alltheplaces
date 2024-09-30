import json
from datetime import datetime, timedelta
from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser


class VirginiaHealthInspectionBlueRidgeSpider(Spider):
    name = "virginia_health_inspection_blue_ridge"
    item_attributes = {}
    start_urls = ["https://inspections.myhealthdepartment.com"]
    custom_settings = {"DOWNLOAD_TIMEOUT": 30}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for area in response.xpath('//a[@title="View Inspections"]/@href').getall():
            if area != "/va-blue-ridge":
                continue
            yield JsonRequest(
                url=response.url,
                callback=self.parse_location_list,
                data={
                    "data": {
                        "path": area.split("/")[-1],
                        "programName": "",
                        "filters": {
                            "date": "{} to {}".format(
                                (datetime.now() - timedelta(weeks=4 * 6)).strftime("%Y-%m-%d"),
                                datetime.now().strftime("%Y-%m-%d"),
                            ),
                            "purpose": "",
                            "city": "",
                            "zip": "",
                        },
                        "start": 0,
                        "count": 500,
                        "searchQueryOverride": None,
                        "searchStr": "",
                        "lat": 0,
                        "lng": 0,
                    },
                    "task": "searchInspections",
                },
            )

    def parse_location_list(self, response: Response, **kwargs: Any) -> Any:
        for inspection in response.json():
            item = DictParser.parse(inspection)

            item["ref"] = inspection["inspectionID"]
            item["extras"]["ref:US:myhealthdepartment"] = inspection["inspectionID"]
            item["name"] = inspection["establishmentName"]

            item["extras"]["check_date"] = datetime.strptime(inspection["inspectionDate"], "%m/%d/%Y").strftime(
                "%Y-%m-%d"
            )

            # categorize the inspection to OSM standards
            if inspection["inspectionType"] == "Fast Food":
                item["extras"]["amenity"] = "fast_food"
            elif inspection["inspectionType"] == "Full Service Restaurant":
                item["extras"]["amenity"] = "restaurant"
            elif inspection["inspectionType"] == "Hospital Food Service":
                item["extras"]["amenity"] = "hospital"
            elif inspection["inspectionType"] == "Educational Facility Food Service":
                item["extras"]["amenity"] = "school"
            else:
                self.crawler.stats.inc_value("{}/unmapped_category/{}".format(self.name, inspection["inspectionType"]))
                continue

            yield item

        if len(response.json()) == 500:
            req = json.loads(response.request.body)
            req["data"]["start"] += req["data"]["count"]
            yield response.request.replace(data=req)
