import re

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours, day_range, sanitise_day
from locations.items import Feature

# Store hours are free text entered by individual franchisees and use a wide
# variety of formats, e.g. "10:30AM - 3AM Daily", "10:30am-12am Sun-Thurs",
# "Sunday - Thursday: 10:30 AM - 2 AM". These two patterns cover every
# format observed across all locations.
TIME = r"\d{1,2}(?::\d{2})?\s*[AaPp][Mm]"
DAY = r"[A-Za-z]+(?:\s*(?:-|to|and)\s*[A-Za-z]+)?"
TIME_FIRST = re.compile(rf"^(?P<t1>{TIME})\s*-\s*(?P<t2>{TIME})\s+(?P<days>.+)$")
DAY_FIRST = re.compile(rf"^(?P<days>{DAY})\s*:\s*(?P<t1>{TIME})\s*-\s*(?P<t2>{TIME})$")


class ToppersPizzaUSSpider(Spider):
    name = "toppers_pizza_us"
    item_attributes = {"brand": "Toppers Pizza", "brand_wikidata": "Q7825113"}
    allowed_domains = ["toppers.com"]
    start_urls = ["https://toppers.com/locations/"]

    def parse(self, response):
        for url in response.css("a.store-details-link::attr(href)").getall():
            yield response.follow(url, callback=self.parse_store)

    def parse_store(self, response):
        item = Feature()
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["website"] = response.url
        item["name"] = response.css(".location-store-name::text").get("").strip()
        item["street_address"] = response.css(".location-street::text").get("").strip()
        item["city"] = response.css(".location-city::text").get("").strip()

        spans = response.css(".location-address > div > span:not(.location-city)::text").getall()
        if len(spans) >= 2:
            item["state"] = spans[0].strip()
            item["postcode"] = spans[1].strip()

        item["phone"] = response.css(".location-phone a::attr(href)").get("").removeprefix("tel:").strip() or None

        if m := re.search(r"latitude:\s*([\-\d.]+),\s*longitude:\s*([\-\d.]+)", response.text):
            item["lat"], item["lon"] = m.group(1), m.group(2)

        item["opening_hours"] = self.parse_hours(response)

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "pizza"

        yield item

    def parse_hours(self, response):
        oh = OpeningHours()
        for line in response.css("div.location-hours ::text").getall():
            line = line.replace("\xa0", " ").strip()
            if not line or line.lower().startswith("hours"):
                continue
            line = line.replace("–", "-").replace("—", "-").rstrip("*").strip()
            line = re.sub(r"\s*&\s*", " and ", line)
            line = re.sub(r"\s+", " ", line)

            if not (m := TIME_FIRST.match(line)) and not (m := DAY_FIRST.match(line)):
                self.logger.warning("Could not parse opening hours line: %r", line)
                continue

            open_time = self.parse_time(m.group("t1"))
            close_time = self.parse_time(m.group("t2"))
            days = self.parse_days(m.group("days"))
            if not open_time or not close_time or not days:
                self.logger.warning("Could not parse opening hours line: %r", line)
                continue

            for day in days:
                oh.add_range(day, open_time, close_time)

        return oh

    @staticmethod
    def parse_time(t: str) -> str | None:
        t = t.replace(" ", "").upper()
        if not (m := re.match(r"^(\d{1,2})(?::(\d{2}))?([AP]M)$", t)):
            return None
        hour = int(m.group(1))
        minute = int(m.group(2) or 0)
        if m.group(3) == "AM":
            if hour == 12:
                hour = 0
        elif hour != 12:
            hour += 12
        return f"{hour:02d}:{minute:02d}"

    @staticmethod
    def parse_days(days_str: str) -> list[str]:
        days_str = days_str.strip().rstrip(".").strip()
        if re.fullmatch(r"(daily|every ?day|all week)", days_str, re.I):
            return DAYS
        parts = [p.strip() for p in re.split(r"\s*(?:-|to|and)\s*", days_str, flags=re.I) if p.strip()]
        if len(parts) == 1:
            return [day] if (day := sanitise_day(parts[0])) else []
        if len(parts) >= 2:
            try:
                return day_range(parts[0], parts[-1])
            except ValueError:
                return []
        return []
