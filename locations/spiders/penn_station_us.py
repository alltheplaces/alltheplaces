import re

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider

TIME_PATTERN = re.compile(r"(\d{1,2}):(\d{2})\s*([ap]m)?", re.I)


class PennStationUSSpider(StructuredDataSpider):
    name = "penn_station_us"
    item_attributes = {"brand": "Penn Station", "brand_wikidata": "Q7163311", "name": "Penn Station"}
    wanted_types = ["FastFoodRestaurant"]
    start_urls = ["https://penn-station.com/locations/"]

    def parse(self, response: Response, **kwargs):
        for href in response.xpath('//a[starts-with(@href, "/locations/")]/@href').getall():
            yield response.follow(href, callback=self.parse_sd)

    def pre_process_data(self, ld_data, **kwargs):
        # Many locations' openingHoursSpecification values are corrupted, with a valid
        # time followed by garbage text (e.g. "10:00pm sun: 11:00am to 9:00pm"), and a
        # single unparseable rule causes LinkedDataParser to drop all hours for the item.
        # Extract just the leading time from each rule, dropping any rule that has none.
        spec = ld_data.get("openingHoursSpecification")
        if not isinstance(spec, list):
            return
        cleaned = []
        for rule in spec:
            if not isinstance(rule, dict):
                continue
            opens = self.clean_time(rule.get("opens"))
            closes = self.clean_time(rule.get("closes"))
            if opens and closes:
                rule["opens"] = opens
                rule["closes"] = closes
                cleaned.append(rule)
        ld_data["openingHoursSpecification"] = cleaned

    @staticmethod
    def clean_time(raw) -> str | None:
        if not isinstance(raw, str):
            return None
        if not (m := TIME_PATTERN.match(raw.strip())):
            return None
        hour, minute, meridiem = int(m.group(1)), m.group(2), m.group(3)
        if meridiem:
            meridiem = meridiem.lower()
            if meridiem == "pm" and hour != 12:
                hour += 12
            elif meridiem == "am" and hour == 12:
                hour = 0
        if hour > 23:
            return None
        return f"{hour:02d}:{minute}"

    def post_process_item(self, item, response, ld_item, **kwargs):
        apply_category(Categories.FAST_FOOD, item)
        item.pop("image", None)  # same brand logo on every location
        if "name" in item and "—" in item["name"]:
            item["branch"] = item.pop("name").split("—", 1)[1].strip()
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        yield item
