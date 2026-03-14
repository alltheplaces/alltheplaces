import json
from typing import Any

import scrapy
from scrapy.http import Response

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

    def parse_details(self, response):
        agency_data = response.json()["AgenciesByCityAndStateResponse"]["GetAgenciesByCityAndStateResult"][
            "_x003C_AgentInformation_x003E_k__BackingField"
        ]["AgentInformation"]

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
                    day = day_time["DayName"]
                    start_time = day_time["StartTime"]
                    end_time = day_time["EndTime"]
                    if (start_time not in ["Closed", None]) and (end_time is not None):
                        item["opening_hours"].add_range(
                            day=day,
                            open_time=start_time.strip()
                            .replace("p.m.", "pm")
                            .replace("a.m.", "am")
                            .replace("a.m", "am"),
                            close_time=end_time.strip()
                            .replace("p.m.", "pm")
                            .replace("a.m.", "am")
                            .replace("p.m", "pm"),
                            time_format="%I:%M %p",
                        )
            except:
                item["opening_hours"] = ""

            yield item
