import re
from itertools import groupby
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, DAYS_EN, DAYS_FULL, OpeningHours, day_range
from locations.items import Feature


def clock(text: str) -> str | None:
    # "9.20am", "4:15pm", "12:00 noon" -> "09:20", "16:15", "12:00"
    m = re.fullmatch(r"(\d{1,2})(?:[.:](\d{2}))?\s*(am|pm|noon)?", text.strip().lower())
    if not m:
        return None
    hour, minute = int(m.group(1)), int(m.group(2) or 0)
    if m.group(3) == "pm" and hour < 12:
        hour += 12
    if m.group(3) == "am" and hour == 12:
        hour = 0
    return f"{hour:02d}:{minute:02d}"


def days_of(text: str) -> list[str]:
    # "Monday-Friday", "Monday to Friday", "Saturday"
    names = re.findall("|".join(DAYS_FULL), text)
    if not names:
        return []
    if len(names) >= 2 and re.search(r"(-|to)", text):
        return day_range(names[0], names[1])
    return [DAYS_EN[n] for n in names]


class GuernseyPostGGSpider(Spider):
    name = "guernsey_post_gg"
    item_attributes = {"operator": "Guernsey Post", "operator_wikidata": "Q5614904"}
    allowed_domains = ["www.guernseypost.com"]
    # Every location is in the page as <div class="location" data-type data-id data-latitude ...>.
    # Types: postbox, postoffice, trail (heritage trail stops), batif (currency), collection (parcels).
    start_urls = ["https://www.guernseypost.com/locations-opening-hours"]
    custom_settings = {"DOWNLOAD_DELAY": 10}  # robots.txt Crawl-delay

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//div[@class="location"]'):
            types = set((location.attrib.get("data-type") or "").split(","))
            name = " ".join(location.xpath('./div[@class="name"]//text()').getall()).strip()
            address = [t.strip() for t in location.xpath('./div[@class="address"]/span/text()').getall()]
            text = "\n".join(t.strip() for t in location.xpath('.//div[@class="tabs"]//text()').getall() if t.strip())
            if "postbox" in types:
                item = self.base_item(location, address)
                item["ref"] = location.attrib["data-id"]
                item["extras"]["description"] = re.sub(r"\s*\(Box no \d+\)", "", name)
                if m := re.search(r"Box no (\d+)", name):
                    item["extras"]["post_box:ref"] = m.group(1)
                if collection_times := self.parse_collection_times(text):
                    item["extras"]["collection_times"] = collection_times
                apply_category(Categories.POST_BOX, item)
                yield item
            elif "postoffice" in types:
                item = self.base_item(location, address)
                item["ref"] = location.attrib["data-id"]
                item["branch"] = re.sub(r"\s*Post Office$", "", name)
                # The first tab is the counter's own opening times; later tabs are other services
                # (e.g. BATIF currency collection hours).
                first_tab = location.xpath('(.//div[@class="tabs"]/div[contains(@class, "tab")])[1]//text()').getall()
                item["opening_hours"] = self.parse_hours("\n".join(t.strip() for t in first_tab if t.strip()))
                apply_category(Categories.POST_OFFICE, item)
                yield item

    @staticmethod
    def base_item(location, address: list[str]) -> Feature:
        item = Feature()
        item["lat"], item["lon"] = location.attrib["data-latitude"], location.attrib["data-longitude"]
        if address and re.fullmatch(r"GY\d[\d A-Z]*", address[-1]):
            item["postcode"] = address[-1]
        parts = [a for a in address if a.upper() != "GUERNSEY" and a != item.get("postcode")]
        if parts:
            item["city"] = parts[-1]
            item["street"] = parts[0] if len(parts) > 1 else None
        return item

    @staticmethod
    def parse_collection_times(text: str) -> str:
        # "Monday-Friday (All Destinations) - 9.20am\nSaturday & Sunday - No collections"
        times = {}
        for line in text.split("\n"):
            days = days_of(line.split(" - ")[0])
            for raw in re.findall(r"\d{1,2}[.:]\d{2}\s*(?:am|pm)|\d{1,2}\s*(?:am|pm)", line.lower()):
                if t := clock(raw):
                    for day in days:
                        times.setdefault(day, set()).add(t)
        by_day = {day: ",".join(sorted(v)) for day, v in times.items()}
        out = []
        for time, days in groupby(DAYS, key=by_day.get):
            if time:
                days = list(days)
                out.append(f"{days[0]}-{days[-1]} {time}" if len(days) > 1 else f"{days[0]} {time}")
        return "; ".join(out)

    @staticmethod
    def parse_hours(text: str) -> OpeningHours:
        # "Monday to Friday: 9:00am to 5:00pm", "Saturday: 8:00am to 12:00 noon." — then a note about
        # BATIF currency collection with its own hours, which aren't the counter's.
        oh = OpeningHours()
        for line in re.split(r"[\n|]", text.split("BATIF")[0]):
            day_text, _, times = line.partition(":")
            # "8.30am" -> "8:30am", "12 noon" -> "12:00pm"
            times = re.sub(r"(\d)\.(\d{2})", r"\1:\2", times)
            times = re.sub(r"12(?::00)?\s*noon", "12:00pm", times, flags=re.IGNORECASE)
            # Days can be a list ("Monday, Tuesday, Thursday and Friday"), which the helper doesn't read.
            for day in days_of(day_text):
                oh.add_ranges_from_string(f"{day} {times}")
        return oh
