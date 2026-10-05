import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature

# The locations page lists each restaurant as a card with its name and a one
# line address, linking to the restaurant's page, where the coordinates sit on
# the Duda map widget and the hours are a day per line.
#
# The site also lists food trucks and a location with no address; those cards
# carry no address line and are skipped.
#
# No brand:wikidata is set because the chain has no Wikidata item.

ADDRESS = re.compile(r"(.+?),\s*([^,]+),\s*([A-Z]{2})\s+(\d{5})")


class SkrimpShackUSSpider(Spider):
    name = "skrimp_shack_us"
    item_attributes = {"brand": "Skrimp Shack"}
    allowed_domains = ["www.skrimpshack.com"]
    start_urls = ["https://www.skrimpshack.com/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        for block in response.xpath('//div[contains(@class, "dmNewParagraph")]'):
            lines = [
                re.sub(r"\s+", " ", " ".join(paragraph.xpath(".//text()").getall())).strip()
                for paragraph in block.xpath("./p")
            ]
            lines = [line for line in lines if line]

            address = next((line for line in lines if ADDRESS.fullmatch(line)), None)
            if not address:
                continue

            item = Feature()
            item["branch"] = next((line for line in lines if line != address), None)
            item["street_address"], item["city"], item["state"], item["postcode"] = ADDRESS.fullmatch(address).groups()

            apply_category(Categories.FAST_FOOD, item)
            item["extras"]["cuisine"] = "seafood"

            page = block.xpath('./following::a[@data-element-type="dButtonLinkId"][1]/@href').get()
            if not page:
                item["ref"] = re.sub(r"[^a-z0-9]+", "-", address.lower()).strip("-")
                yield item
                continue

            item["ref"] = page.strip("/")
            item["website"] = response.urljoin(page)
            yield response.follow(page, callback=self.parse_location, cb_kwargs={"item": item})

    def parse_location(self, response: Response, item: Feature) -> Iterable[Feature]:
        item["lat"] = response.xpath("//div[@data-lat]/@data-lat").get()
        item["lon"] = response.xpath("//div[@data-lng]/@data-lng").get()
        item["phone"] = response.xpath('//a[starts-with(@href, "tel:")]/@href').re_first(r"tel:(.+)")

        item["opening_hours"] = self.parse_opening_hours(response)

        yield item

    @staticmethod
    def parse_opening_hours(response: Response) -> OpeningHours | None:
        """The hours read "Monday: 11 AM-9 PM" or "Mon-Sat: 11 AM-9 PM"."""
        oh = OpeningHours()

        for line in response.xpath("//p"):
            text = re.sub(r"\s+", " ", " ".join(line.xpath(".//text()").getall()))
            text = text.replace("\u2013", "-").replace("\u2014", "-").replace("\xa0", " ").strip()

            # "Monday: 11 AM-9 PM", or a range such as "Mon-Sat: 11 AM-9 PM".
            if not (rule := re.fullmatch(r"([A-Za-z]{3,9})\s*(?:-\s*([A-Za-z]{3,9}))?\s*:\s*(.+)", text)):
                continue
            start_day, end_day = sanitise_day(rule.group(1)), sanitise_day(rule.group(2) or rule.group(1))
            if not start_day or not end_day:
                continue
            days = day_range(start_day, end_day)

            hours = rule.group(3).strip()
            if "closed" in hours.lower():
                for day in days:
                    oh.set_closed(day)
                continue
            if times := re.search(r"(\d{1,2}(?::\d{2})?\s*[AP]M)\s*-\s*(\d{1,2}(?::\d{2})?\s*[AP]M)", hours, re.I):
                oh.add_days_range(
                    days,
                    SkrimpShackUSSpider.normalise_time(times.group(1)),
                    SkrimpShackUSSpider.normalise_time(times.group(2)),
                    time_format="%I:%M%p",
                )

        return oh if oh else None

    @staticmethod
    def normalise_time(value: str) -> str:
        value = value.replace(" ", "").upper()
        return value if ":" in value else re.sub(r"(\d+)", r"\1:00", value, count=1)
