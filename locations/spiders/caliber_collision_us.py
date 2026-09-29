import re
from datetime import UTC, datetime
from typing import AsyncIterator

from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, apply_category, apply_yes_no
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
        services = {key for service in location.get("serviceType") or [] for key in service}
        if not services or services == {"mobileGlass"}:
            return  # Glass market pages and mobile glass service areas, not premises

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
        elif location.get("status") == "inactive" and not (start_date and start_date > datetime.now(UTC)):
            set_closed(item)  # Inactive centres with a future openDate are upcoming openings, left open

        apply_category(Categories.SHOP_CAR_REPAIR, item)
        apply_yes_no(Extras.VEHICLE_BODY_REPAIR_SERVICES, item, bool(services & {"collision", "fleetCare"}), False)
        apply_yes_no(Extras.VEHICLE_WINDSCREEN_REPLACEMENT_SERVICES, item, bool(services & {"glass", "mobileGlass"}))
        apply_yes_no(Extras.VEHICLE_CAR_REPAIR_SERVICES, item, "autoCare" in services)

        if path := location.get("urlMap"):
            item["website"] = response.urljoin(path)
        else:
            del item["website"]

        yield item

    def parse_date(self, date_str: str | None) -> datetime | None:
        if not date_str:
            return None
        if match := millisecond_date.match(date_str):
            return datetime.fromtimestamp(int(match.group(1)) / 1000, UTC)
        if (match := mdy_date.match(date_str)) or (match := iso_date.match(date_str)):
            return datetime(**{k: int(v) for k, v in match.groupdict().items()}, tzinfo=UTC)
        self.logger.info(f"Unknown date format {date_str!r}")
        return None
