import re
from datetime import datetime
from typing import AsyncIterator

from scrapy.http import JsonRequest

from locations.categories import Extras, apply_yes_no
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import SocialMedia, set_closed, set_social_media
from locations.json_blob_spider import JSONBlobSpider

millisecond_date = re.compile(r"/Date\((\d+)\)/")
mdy_date = re.compile(r"(?P<month>\d+)/(?P<day>\d+)/(?P<year>\d+)")
iso_date = re.compile(r"(?P<year>\d+)-(?P<month>\d+)-(?P<day>\d+)T(?P<hour>\d+):(?P<minute>\d+):(?P<second>\d+)")


class CaliberCollisionUSSpider(JSONBlobSpider):
    name = "caliber_collision_us"
    item_attributes = {"brand": "Caliber Collision", "brand_wikidata": "Q109329782"}
    locations_key = "contentlets"
    custom_settings = {"DOWNLOAD_TIMEOUT": 30}

    async def start(self) -> AsyncIterator[JsonRequest]:
        data = {"size": 100000, "query": {"bool": {"must": {"query_string": {"query": "+contentType:Center"}}}}}
        yield JsonRequest("https://www.caliber.com/api/es/search", data=data)

    def post_process_item(self, item, response, location):
        item["branch"] = location["title"]
        item["extras"]["alt_ref"] = location.get("centerId")
        item["extras"]["fax"] = location.get("faxNumber")
        if "zip" in location:
            item["postcode"] = str(location["zip"])
        item["state"] = location.get("state")
        set_social_media(item, SocialMedia.YELP, location.get("yelpUrl"))

        if "metaTitle" in location and "|" in location["metaTitle"]:
            item["name"] = location["metaTitle"].split("|")[1].strip()
        else:
            del item["name"]

        oh = OpeningHours()
        for day in map(str.lower, DAYS_FULL):
            if location.get(f"{day}HoursClose") == location.get(f"{day}HoursOpen") == "1970-01-01 00:00:00.0":
                oh.set_closed(day)
            else:
                oh.add_range(
                    day,
                    location.get(f"{day}HoursClose"),
                    location.get(f"{day}HoursOpen"),
                    time_format="%Y-%m-%d %H:%M:%S.0",
                )
        item["opening_hours"] = oh

        if start_date := self.parse_date(location.get("openDate")):
            item["extras"]["start_date"] = start_date.strftime("%Y-%m-%d")

        if location.get("status") == "closed" or location.get("closeDate"):
            set_closed(item, self.parse_date(location.get("closeDate")))
        elif location.get("status") == "inactive" and not (start_date and start_date > datetime.now()):
            set_closed(item)  # An inactive location with a future openDate is an upcoming opening, not a closure

        if services := {key for service in location.get("serviceType") or [] for key in service}:
            body_repair = bool(services & {"collision", "fleetCare"})
            glass = bool(services & {"glass", "mobileGlass"})
            apply_yes_no(Extras.VEHICLE_BODY_REPAIR_SERVICES, item, body_repair, apply_positive_only=not glass)
            apply_yes_no(Extras.VEHICLE_WINDSCREEN_REPLACEMENT_SERVICES, item, glass)
            apply_yes_no(Extras.VEHICLE_CAR_REPAIR_SERVICES, item, "autoCare" in services)

        if path := location.get("urlMap"):
            item["website"] = response.urljoin(path)
        else:
            del item["website"]

        yield item

    def parse_date(self, date_str: str | None) -> datetime | None:
        if not date_str:
            return None
        try:
            if match := millisecond_date.match(date_str):
                return datetime.fromtimestamp(int(match.group(1)) / 1000)
            if (match := mdy_date.match(date_str)) or (match := iso_date.match(date_str)):
                return datetime(**{k: int(v) for k, v in match.groupdict().items()})
        except (ValueError, OverflowError, OSError):
            pass  # Shaped like a date but not a real one (e.g. month 13, or a timestamp out of range)
        self.logger.info(f"Unknown date format {date_str!r}")
        return None
