import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature

# The site is built with Squarespace and has no locator data of its own: each
# restaurant has a page, linked from the map page, with the address, phone and
# hours as plain text blocks.
#
# The hours are two parallel runs of paragraphs, the day names first and then
# the times in the same order.
#
# No coordinates are published.
#
# No brand:wikidata is set because the chain has no Wikidata item.

ADDRESS = re.compile(r"(.+?),\s*([^,]+),\s*([A-Z]{2})\s+(\d{5})")
PHONE = re.compile(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")


class HalfShellOysterHouseUSSpider(Spider):
    name = "half_shell_oyster_house_us"
    item_attributes = {"brand": "Half Shell Oyster House"}
    allowed_domains = ["www.halfshelloysterhouse.com"]
    start_urls = ["https://www.halfshelloysterhouse.com/maplocations"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        # The links are root relative, and the page also links to the menus,
        # careers and other site pages, which carry no address.
        for path in sorted(set(response.xpath("//a/@href").re(r"^/[a-z0-9-]+$"))):
            yield response.follow(path, callback=self.parse_location)

    def parse_location(self, response: Response) -> Iterable[Feature]:
        lines = [
            re.sub(r"\s+", " ", " ".join(line.xpath(".//text()").getall())).strip()
            for line in response.xpath('//div[contains(@class, "sqs-html-content")]//p')
        ]
        lines = [line for line in lines if line]

        address = next((match for line in lines if (match := ADDRESS.fullmatch(line))), None)
        if not address:
            return

        item = Feature()
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["website"] = response.url
        item["street_address"], item["city"], item["state"], item["postcode"] = address.groups()
        # The page titles are marketing lines ("Best Seafood in Biloxi"), so
        # the branch is the city, and the casino restaurant is noted as such.
        item["branch"] = item["city"]
        if "casino" in item["ref"]:
            item["located_in"] = "Hard Rock Casino"
        if phone := next((PHONE.fullmatch(line) for line in lines if PHONE.fullmatch(line)), None):
            item["phone"] = phone.group(0)

        item["opening_hours"] = self.parse_opening_hours(lines)

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "seafood"

        yield item

    @staticmethod
    def parse_opening_hours(lines: list[str]) -> OpeningHours | None:
        """The day names are listed first, then the times in the same order."""
        oh = OpeningHours()

        days = [DAYS_EN[line.title()] for line in lines if line.title() in DAYS_EN]
        times = [
            match
            for line in lines
            if (match := re.fullmatch(r"(\d{1,2}(?::\d{2})?\s*[ap]m)\s*-\s*(\d{1,2}(?::\d{2})?\s*[ap]m)", line, re.I))
        ]
        if not days or len(days) != len(times):
            return None

        for day, rule in zip(days, times):
            oh.add_range(
                day,
                HalfShellOysterHouseUSSpider.normalise_time(rule.group(1)),
                HalfShellOysterHouseUSSpider.normalise_time(rule.group(2)),
                time_format="%I:%M%p",
            )

        return oh if oh else None

    @staticmethod
    def normalise_time(value: str) -> str:
        value = value.replace(" ", "").upper()
        return value if ":" in value else re.sub(r"(\d+)", r"\1:00", value, count=1)
