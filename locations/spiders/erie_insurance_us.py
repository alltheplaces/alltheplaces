import json
from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class ErieInsuranceUSSpider(scrapy.Spider):
    name = "erie_insurance_us"
    item_attributes = {
        "brand": "Erie Insurance",
        "brand_wikidata": "Q5388314",
    }
    start_urls = ["https://www.erieinsurance.com/api/statescities"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for state in response.json()["AgencyStatesAndCitiesResponse"]["GetAgencyStatesAndCitiesResult"][
            "KeyValueOfstringArrayOfstringty7Ep6D1"
        ]:
            if isinstance(state["Value"]["string"], str):
                state["Value"]["string"] = [state["Value"]["string"]]
            for city in state["Value"]["string"]:
                yield scrapy.Request(
                    url=f"https://www.erieinsurance.com/api/agentsbystatescities?state={state['Key']}&city={city.lower()}",
                    callback=self.parse_details,
                )

    def parse_details(self, response: Response, **kwargs: Any) -> Any:
        backing_field = response.json()["AgenciesByCityAndStateResponse"]["GetAgenciesByCityAndStateResult"][
            "_x003C_AgentInformation_x003E_k__BackingField"
        ]
        if not isinstance(backing_field, dict):
            return
        agency_data = backing_field["AgentInformation"]

        if isinstance(agency_data, dict):
            agency_data = [agency_data]
        for agency in agency_data:
            agency.update(agency["Address"].pop("GeoCode"))
            item = DictParser.parse(agency)
            item["ref"] = agency.get("AgencyAccountNumber")
            item["opening_hours"] = OpeningHours()
            try:
                for day_time in json.loads(agency["AgencyInfo"]["BusinessHoursOperationDescription"]).get(
                    "HoursOfOperation", ""
                ):
                    if day_time["StartTime"] and day_time["EndTime"]:
                        item["opening_hours"].add_range(
                            day=day_time["DayName"],
                            open_time=day_time["StartTime"].strip().replace(".", ""),
                            close_time=day_time["EndTime"].strip().replace(".", ""),
                            time_format="%I:%M %p",
                        )
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                item["opening_hours"] = None

            apply_category(Categories.OFFICE_INSURANCE, item)
            yield item
