import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature


class CodysOriginalRoadhouseUSSpider(Spider):
    name = "codys_original_roadhouse_us"
    item_attributes = {"brand": "Cody's Original Roadhouse"}
    allowed_domains = ["www.codysoriginalroadhouse.com"]
    start_urls = ["https://www.codysoriginalroadhouse.com/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        for link in response.xpath("//a[@href]"):
            if re.fullmatch(r"[A-Z .'-]+, [A-Z]{2}", link.xpath("normalize-space(string())").get() or ""):
                yield response.follow(link.xpath("@href").get(), callback=self.parse_location)

    def parse_location(self, response: Response) -> Iterable[Feature]:
        lines = [
            re.sub(r"\s+", " ", text).strip()
            for text in response.xpath('//*[contains(@class, "wixui-rich-text__text")]/text()').getall()
            if text.strip()
        ]

        item = Feature()
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["website"] = response.url
        # Titles are "BAY PINES, FL | Cody's Original Roadhouse".
        branch = response.xpath("//title/text()").re_first(r"^([^,|]+)") or item["ref"]
        item["branch"] = branch.strip().title()

        for line in lines:
            # Some pages append ", USA" to the address line.
            if address := re.fullmatch(r"(.+?),\s*([^,]+),\s*([A-Z]{2})\s+(\d{5})(?:,\s*USA)?", line):
                item["street_address"], item["city"], item["state"], item["postcode"] = [
                    group.strip() for group in address.groups()
                ]
                break
        else:
            return

        # Written as "941 -727-6700" or "(727) 345-1022".
        if phone := re.search(r"\(?\d{3}\)?\s*[-.\s]\s*\d{3}\s*-\s*\d{4}", " ".join(lines)):
            item["phone"] = phone.group(0)

        item["opening_hours"] = self.parse_opening_hours(lines)

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "steak_house"

        yield item

    @staticmethod
    def parse_opening_hours(lines: list[str]) -> OpeningHours | None:
        """Parses lines such as "Monday - Friday: 3pm - 10pm"."""
        oh = OpeningHours()

        for line in lines:
            line = line.replace("\u2013", "-").replace("\u2014", "-")
            if not (times := re.search(r"(\d{1,2}(?::\d{2})?\s*[ap]m)\s*-\s*(\d{1,2}(?::\d{2})?\s*[ap]m)", line, re.I)):
                continue

            day_names = []
            for token in re.split(r"&|\band\b", line[: times.start()].strip(" :")):
                token = token.strip()
                if "-" in token:
                    start, end = [sanitise_day(part) for part in token.split("-", 1)]
                    if start and end:
                        day_names.extend(day_range(start, end))
                elif day := sanitise_day(token):
                    day_names.append(day)

            if day_names:
                oh.add_days_range(
                    day_names,
                    times.group(1),
                    times.group(2),
                    time_format=["%I:%M%p", "%I:%M %p", "%I%p", "%I %p"],
                )

        return oh if oh.as_opening_hours() else None
