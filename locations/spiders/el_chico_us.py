import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature

# The locations page lists each restaurant as a row holding the branch, the
# address, the phone and the hours, with the hours written as "Sun - Thur
# 11:00am - 9:00pm" and "Fri & Sat ...".
#
# No coordinates are published.
#
# No brand:wikidata is set because the chain has no Wikidata item.

DAYS = {
    "M": "Mo",
    "MON": "Mo",
    "T": "Tu",
    "TU": "Tu",
    "TUE": "Tu",
    "TUES": "Tu",
    "W": "We",
    "WED": "We",
    "TH": "Th",
    "THU": "Th",
    "THUR": "Th",
    "THURS": "Th",
    "F": "Fr",
    "FRI": "Fr",
    "S": "Sa",
    "SA": "Sa",
    "SAT": "Sa",
    "SU": "Su",
    "SUN": "Su",
}

# Three restaurants put the whole address on one line with no comma before the
# city: "7621 Baker Blvd Richland Hills, TX 76118".
ADDRESS = re.compile(r"(.+?),\s*([A-Z]{2})\s+(\d{5})(?:-\d{4})?")


class ElChicoUSSpider(Spider):
    name = "el_chico_us"
    item_attributes = {"brand": "El Chico"}
    allowed_domains = ["www.elchico.com"]
    start_urls = ["https://www.elchico.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for row in response.xpath('//div[@class="single-location"]'):
            branch = re.sub(r"\s+", " ", row.xpath('.//div[@class="location-name"]/text()').get("")).strip()
            lines = [
                re.sub(r"\s+", " ", line).strip()
                for line in row.xpath('.//div[@class="location-address"]//text()').getall()
                if line.strip()
            ]
            locality = next((match for line in lines if (match := ADDRESS.fullmatch(line))), None)
            if locality and not re.search(r"\d", locality.group(1)):
                street = ", ".join(lines[: lines.index(locality.group(0))])
                city = locality.group(1)
            elif locality:
                # "7621 Baker Blvd Richland Hills, TX 76118" has no comma before
                # the city, so the branch name is stripped off the end instead.
                head = locality.group(1)
                if not branch or not head.lower().endswith(branch.lower()):
                    continue
                street, city = head[: -len(branch)].strip(" ,"), branch
            else:
                continue

            item = Feature()
            item["branch"] = branch
            item["website"] = row.xpath(".//a[@href]/@href").get()
            item["ref"] = (item["website"] or "").rstrip("/").rsplit("/", 1)[-1]
            item["city"], item["state"], item["postcode"] = city, locality.groups()[-2], locality.groups()[-1]
            item["street_address"] = street
            item["phone"] = row.xpath('.//div[@class="tel"]//a/text()').get()

            item["opening_hours"] = self.parse_opening_hours(row.xpath('.//div[@class="my-hours"]//text()').getall())

            apply_category(Categories.RESTAURANT, item)
            item["extras"]["cuisine"] = "mexican;tex-mex"

            yield item

    @staticmethod
    def parse_opening_hours(values: list[str]) -> OpeningHours | None:
        """The hours read "Sun - Thur" then "11:00am - 9:00pm", a pair at a time."""
        oh = OpeningHours()

        values = [re.sub(r"\s+", " ", value).replace("\u2013", "-").strip() for value in values]
        values = [value for value in values if value]

        for label, hours in zip(values, values[1:]):
            # "Sun - Thurs", "M-Th:", "F & S:", "Mon - Thurs & Sat" or a day on
            # its own.
            days = []
            for part in re.split(r"&|,|\band\b", label.rstrip(":")):
                tokens = [
                    day
                    for token in part.split("-")
                    if (day := DAYS.get(token.strip().upper()) or sanitise_day(token.strip()))
                ]
                if len(tokens) == 2:
                    days.extend(day_range(tokens[0], tokens[1]))
                else:
                    days.extend(tokens)
            if not days:
                continue
            if times := re.fullmatch(r"(\d{1,2}(?::\d{2})?\s*[ap]m)\s*-\s*(\d{1,2}(?::\d{2})?\s*[ap]m)", hours, re.I):
                oh.add_days_range(
                    days,
                    ElChicoUSSpider.normalise_time(times.group(1)),
                    ElChicoUSSpider.normalise_time(times.group(2)),
                    time_format="%I:%M%p",
                )

        return oh if oh else None

    @staticmethod
    def normalise_time(value: str) -> str:
        value = value.replace(" ", "").upper()
        return value if ":" in value else re.sub(r"(\d+)", r"\1:00", value, count=1)
