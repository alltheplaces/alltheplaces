from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser


class VirginiaHealthInspectionBlueRidgeSpider(Spider):
    name = "virginia_health_inspection_blue_ridge"
    item_attributes = {}
    start_urls = ["https://inspections.myhealthdepartment.com"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(
                url=url,
                callback=self.parse_location_list,
                data={
                    "data": {
                        "path": "va-blue-ridge",
                        "programName": "",
                        # TODO: make the date dynamic
                        "filters": {"date": "2024-01-01 to 2024-09-27", "purpose": "", "city": "", "zip": ""},
                        "start": 0,
                        "count": 2000,
                        "searchQueryOverride": None,
                        "searchStr": "",
                        "lat": 0,
                        "lng": 0,
                    },
                    "task": "searchInspections",
                },
            )

    def parse_location_list(self, response):
        for inspection in response.json():
            item = DictParser.parse(inspection)

            item["ref"] = inspection["inspectionID"]
            item["name"] = inspection["establishmentName"]

            item["extras"] = ({"inspectionDate": inspection["inspectionDate"]},)

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
                return

            yield item
