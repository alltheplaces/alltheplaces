import re
from json import dumps
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import FormRequest, Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours


class MacCosmeticsSpider(Spider):
    name = "mac_cosmetics"
    item_attributes = {"brand": "MAC Cosmetics", "brand_wikidata": "Q2624442"}
    allowed_domains = ["maccosmetics.com"]
    only_hour = re.compile(r"^(\d\d?)([ap]m)", re.IGNORECASE)
    colon_missing = re.compile(r"^(\d?\d)(\d\d[ap]m)", re.IGNORECASE)
    am_missing = re.compile(r"^(\d?\d(:\d\d)?)$")
    whitespace_before_am = re.compile(r"\s([ap]m)", re.IGNORECASE)
    time_dot = re.compile(r"(\d?\d)\.(\d\d[ap]m)", re.IGNORECASE)
    am_dot = re.compile(r"([ap]m)\.", re.IGNORECASE)
    pm_with_24h = re.compile(r"(1[3-9]|2\d)((?::\d\d)?\s*pm)")
    re_period = re.compile(r"\s*[,/&]\s*")
    re_range = re.compile(r"\s*(?:-|–| to )\s*")

    async def start(self) -> AsyncIterator[FormRequest]:
        jsonrpc = [
            {
                "method": "locator.doorsandevents",
                "id": 3,
                "params": [
                    {
                        "fields": "DOOR_ID,DOORNAME,EVENT_NAME,SUB_HEADING,EVENT_START_DATE,EVENT_END_DATE,"
                        "EVENT_IMAGE,EVENT_FEATURES,EVENT_TIMES,SERVICES,STORE_HOURS,ADDRESS,ADDRESS2,"
                        "STATE_OR_PROVINCE,CITY,REGION,COUNTRY,ZIP_OR_POSTAL,PHONE1,PHONE2,"
                        "STORE_TYPE,LONGITUDE,LATITUDE,COMMENTS",
                        "country": "United States",
                        "latitude": 0.0,
                        "longitude": 0.0,
                        "uom": "mile",
                        "region_id": 0,
                        "radius": 25000,
                    }
                ],
            }
        ]
        yield FormRequest(
            "https://www.maccosmetics.com/rpc/jsonrpc.tmpl?dbgmethod=locator.doorsandevents",
            method="POST",
            formdata={"JSONRPC": dumps(jsonrpc)},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        stores = response.json()[0]["result"]["value"]["results"]
        rename = {
            "DOOR_ID": "ref",
            "DOORNAME": "name",
            "ADDRESS": "street_address",
            "ADDRESS2": "street2",
            "ZIP_OR_POSTAL": "postcode",
            "PHONE1": "phone",
        }
        for feature in stores.values():
            for old, new in rename.items():
                if old in feature:
                    feature[new] = feature.pop(old)
            item = DictParser.parse(feature)
            if len(feature.get("STORE_TYPE", "")) > 0:
                item["extras"]["store_type"] = feature["STORE_TYPE"]
            any_open = True
            if "STORE_HOURS" in feature and isinstance(feature["STORE_HOURS"], list):
                any_open, opening_hours = self.parse_opening_hours(feature)
                item["opening_hours"] = opening_hours
            if any_open and not item["name"].endswith("- Closed"):
                yield item

    def parse_opening_hours(self, feature):
        any_open = False
        opening_hours = OpeningHours()
        for day_definition in feature["STORE_HOURS"]:
            try:
                day = DAYS_EN[day_definition["day"]]
                if (
                    day_definition.get("hours") is not None
                    and len(day_definition["hours"]) > 0
                    and day_definition["hours"].lower() != "closed"
                ):
                    for period in self.re_period.split(day_definition["hours"]):
                        try:
                            opening_time, closing_time = self.re_range.split(period.strip())
                            if "m" in opening_time.lower() or "m" in closing_time.lower():  # 12-hour format
                                opening_time = self.fix_time_format(opening_time)
                                closing_time = self.fix_time_format(closing_time)
                                try:
                                    opening_hours.add_range(day, opening_time, closing_time, "%I:%M%p")
                                except ValueError:
                                    self.logger.warning(
                                        "Invalid opening hours format <%s>, <%s>", opening_time, closing_time
                                    )
                            else:  # 24-hour format
                                try:
                                    opening_hours.add_range(day, opening_time, closing_time, "%H:%M")
                                except ValueError:
                                    self.logger.warning(
                                        "Invalid opening hours format <%s>, <%s>", opening_time, closing_time
                                    )
                            any_open = True
                        except ValueError:
                            self.logger.warning("Invalid opening hours format: '%s'", period)
            except KeyError:
                self.logger.warning(
                    "Bad \"day\" in the opening hours definition: '%s', for store '%s'",
                    day_definition["day"],
                    feature.get("name"),
                )
        return any_open, opening_hours

    def fix_time_format(self, time: str) -> str:
        time = self.whitespace_before_am.sub(r"\1", time)
        time = time.replace("mn", "pm")
        time = self.am_missing.sub(r"\1am", time)
        time = self.am_dot.sub(r"\1", time)
        time = self.time_dot.sub(r"\1:\2", time)
        time = self.only_hour.sub(r"\1:00\2", time)
        time = self.colon_missing.sub(r"\1:\2", time)
        match = self.pm_with_24h.match(time)
        if match:
            time = f"{int(match.group(1)) - 12:02d}{match.group(2)}"
        return time
