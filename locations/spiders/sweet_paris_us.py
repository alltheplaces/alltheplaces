import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines

# The locations page is a Webflow collection: each cafe is a card carrying its
# status in data-status ("Existing", "New" or "Coming Soon") and its address as
# "street\ncity, state postcode". Both status badges are rendered on every
# card, so data-status is what identifies cafes that have not opened.
#
# Phone and hours are only on each cafe's page. The page's JSON-LD block is not
# valid JSON (a raw newline, a missing comma and a trailing comma), so the phone
# is read from the page text, and the hours are two parallel columns of days
# and times.
#
# No coordinates are published. No brand:wikidata is set because the chain has
# no Wikidata item.

# The days column uses one and two letter abbreviations.
DAYS = {"M": "Mo", "T": "Tu", "W": "We", "Th": "Th", "F": "Fr", "Sa": "Sa", "Su": "Su"}


class SweetParisUSSpider(Spider):
    name = "sweet_paris_us"
    item_attributes = {"brand": "Sweet Paris Crêperie & Café"}
    allowed_domains = ["www.sweetparis.com"]
    start_urls = ["https://www.sweetparis.com/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        for location in response.xpath('//a[contains(@class, "element_location")]'):
            if location.xpath("@data-status").get() == "Coming Soon":
                continue

            item = Feature()
            item["ref"] = location.xpath("@href").get("").rstrip("/").rsplit("/", 1)[-1]
            item["branch"] = location.xpath(".//h3/text()").get()
            item["website"] = response.urljoin(location.xpath("@href").get())

            lines = [
                line.strip()
                for line in (location.xpath('.//div[@class="location_description"]/text()').get() or "").split("\n")
                if line.strip()
            ]
            # "Houston, Texas 77024". The collection also includes a cafe in
            # Mexico, whose address has no US postcode and is skipped.
            if not lines or not (locality := re.fullmatch(r"(.+?),\s*([A-Za-z .]+?)\s+(\d{5})", lines[-1])):
                continue
            item["city"], item["state"], item["postcode"] = [part.strip() for part in locality.groups()]
            item["street_address"] = merge_address_lines(lines[:-1])

            apply_category(Categories.CAFE, item)
            item["extras"]["cuisine"] = "crepe;french"

            yield response.follow(item["website"], callback=self.parse_cafe, cb_kwargs={"item": item})

    def parse_cafe(self, response: Response, item: Feature) -> Iterable[Feature]:
        if phone := re.search(r'"telephone":\s*"([^"]+)"', response.text):
            item["phone"] = phone.group(1)

        columns = response.xpath('//div[@class="location-header_hours-wrapper"]/div')
        if len(columns) == 2:
            oh = OpeningHours()
            days = [day.strip() for day in columns[0].xpath(".//p/text()").getall()]
            times = [time.strip() for time in columns[1].xpath(".//p/text()").getall()]
            for day, time in zip(days, times):
                if not (day := DAYS.get(day.rstrip(":").strip())):
                    continue
                if rule := re.fullmatch(
                    r"(\d{1,2}(?::\d{2})?\s*[ap]m)\s*[\u2013-]\s*(\d{1,2}(?::\d{2})?\s*[ap]m)", time, re.I
                ):
                    oh.add_range(
                        day, self.normalise_time(rule.group(1)), self.normalise_time(rule.group(2)), "%I:%M%p"
                    )
            item["opening_hours"] = oh if oh else None

        yield item

    @staticmethod
    def normalise_time(value: str) -> str:
        value = value.replace(" ", "").upper()
        return value if ":" in value else re.sub(r"(\d+)", r"\1:00", value, count=1)
