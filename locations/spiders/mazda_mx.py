import json
import re

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_ES, OpeningHours, day_range, sanitise_day
from locations.items import Feature, SocialMedia, set_social_media
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.mazda_jp import MAZDA_SHARED_ATTRIBUTES

HOURS_LINE = re.compile(r"([^:<]+?):\s*([^<]+)")
TIME_RANGE = re.compile(r"(\d{1,2}:\d\d)\s*a\s*(\d{1,2}:\d\d)")


class MazdaMXSpider(JSONBlobSpider):
    name = "mazda_mx"
    item_attributes = MAZDA_SHARED_ATTRIBUTES
    allowed_domains = ["www.mazda.mx"]
    start_urls = ["https://www.mazda.mx/localizar-distribuidor"]

    def extract_json(self, response):
        return json.loads(response.css("script#dealers-data::text").get())

    def pre_process_data(self, feature: dict) -> None:
        if feature.get("Address"):
            feature["Address"] = re.sub(r"<br\s*/?>", ", ", feature["Address"]).strip()

    def post_process_item(self, item: Feature, response, feature: dict):
        item["website"] = feature.get("Website") or response.url
        # Some records list an extension after a colon, or several numbers separated by
        # commas or whitespace before a second "(area code)"; only the first (main)
        # number is kept.
        item["phone"] = self.first_number(feature.get("Phone"))

        if whatsapp := self.first_number(feature.get("WhatsApp")):
            set_social_media(item, SocialMedia.WHATSAPP, whatsapp)

        if oh := self.parse_hours(feature.get("HoursOfOperation")):
            item["opening_hours"] = oh

        if feature.get("IsAgency"):
            apply_category(Categories.SHOP_CAR, item)
        else:
            apply_category(Categories.SHOP_CAR_REPAIR, item)

        if feature.get("HasServiceShop") or feature.get("HasCollisionCenter") or feature.get("HasQuickFix"):
            apply_yes_no(Extras.VEHICLE_CAR_REPAIR_SERVICES, item, True)

        yield item

    @staticmethod
    def first_number(value: str | None) -> str | None:
        if not value:
            return None
        return re.split(r"[,:]|\s{2,}(?=\()", value)[0].strip() or None

    def parse_hours(self, text: str | None) -> OpeningHours | None:
        if not text:
            return None
        text = text.replace("&nbsp;", " ")
        text = re.sub(r"<[^>]+>", "|", text)

        oh = OpeningHours()
        found = False
        for chunk in text.split("|"):
            m = HOURS_LINE.match(chunk.strip())
            if not m:
                continue
            days_part, times_part = m.group(1).strip(), m.group(2).strip()

            if "-" in days_part:
                start_day, end_day = days_part.split("-", 1)
            elif " a " in days_part:
                start_day, end_day = days_part.split(" a ", 1)
            elif " y " in days_part:
                # e.g. "Sáb y Dom" (Sat and Sun); treated as a range since the two days
                # are adjacent in the week.
                start_day, end_day = days_part.split(" y ", 1)
            else:
                start_day, end_day = days_part, None

            start_day = sanitise_day(start_day, DAYS_ES)
            end_day = sanitise_day(end_day, DAYS_ES) if end_day else None
            if not start_day:
                continue
            days = day_range(start_day, end_day) if end_day else [start_day]

            for open_time, close_time in TIME_RANGE.findall(times_part):
                for day in days:
                    oh.add_range(day, open_time, close_time)
                    found = True

        return oh if found else None
