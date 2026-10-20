import re
from typing import Any, Iterable

from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines

# The locations page links to a page per restaurant, each carrying a Location
# block with the address and phone and an Hours block written as free text such
# as "SUN - THURS, 4 - 9 PM".
#
# No coordinates are published: the address links are goo.gl short links that
# would need resolving one by one.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class OceanPrimeUSSpider(Spider):
    name = "ocean_prime_us"
    item_attributes = {"brand": "Ocean Prime"}
    allowed_domains = ["ocean-prime.com"]
    start_urls = ["https://ocean-prime.com/locations-menus/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        for path in set(response.xpath('//a[@class="explore-link"]/@href').getall()):
            yield response.follow(path, callback=self.parse_location)

    def parse_location(self, response: Response) -> Iterable[Feature]:
        address = response.xpath('//a[@class="address"]')
        lines = [re.sub(r"\s+", " ", line).strip() for line in address.xpath(".//text()").getall()]
        lines = [line for line in lines if line]
        # "124 South 15th Street" / "Philadelphia, PA 19102", but the state is
        # sometimes spelled out or written as "D.C.".
        if not lines or not (locality := re.fullmatch(r"(.+),\s*([A-Za-z.\s]+?)\s+(\d{5})", lines[-1])):
            return

        item = Feature()
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["branch"] = response.xpath("//h1/text()").get() or item["ref"]
        item["website"] = response.url
        item["street_address"] = merge_address_lines(lines[:-1])
        item["city"], state, item["postcode"] = [part.strip() for part in locality.groups()]
        # Washington writes its state as "D.C.".
        item["state"] = "DC" if state.replace(".", "").upper() == "DC" else state
        item["phone"] = response.xpath('//a[starts-with(@href, "tel:")]/text()').get()

        item["opening_hours"] = self.parse_opening_hours(response)

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "seafood;steak_house"

        yield item

    @staticmethod
    def parse_opening_hours(response: Selector) -> OpeningHours | None:
        """
        Parses rules such as "SUN - THURS, 4 - 9 PM", one per line, under a
        "Lunch" or "Dinner" heading.
        """
        oh = OpeningHours()

        for line in response.xpath('//div[@class="location-hours"]//text()').getall():
            line = re.sub(r"\s+", " ", line).strip().replace("\u2013", "-").replace("\u2014", "-")
            if not (times := re.search(r"(\d{1,2}(?::\d{2})?)\s*-\s*(\d{1,2}(?::\d{2})?)\s*([AP]M)", line, re.I)):
                continue

            day_names = []
            for token in re.split(r"&|,|\band\b", line[: times.start()]):
                token = token.strip()
                if "-" in token:
                    start, end = [sanitise_day(part) for part in token.split("-", 1)]
                    if start and end:
                        day_names.extend(day_range(start, end))
                elif day := sanitise_day(token):
                    day_names.append(day)

            if not day_names:
                continue

            # The meridiem is given once, at the end of the range, so an
            # opening hour later than the closing hour is in the morning —
            # except noon, which stays PM.
            open_hour, close_hour, meridiem = times.groups()
            open_value, close_value = int(open_hour.split(":")[0]), int(close_hour.split(":")[0])
            opens = OceanPrimeUSSpider.normalise_time(
                open_hour,
                "AM" if meridiem.upper() == "PM" and open_value != 12 and open_value > close_value else meridiem,
            )
            oh.add_days_range(
                day_names, opens, OceanPrimeUSSpider.normalise_time(close_hour, meridiem), time_format="%I:%M%p"
            )

        return oh if oh.as_opening_hours() else None

    @staticmethod
    def normalise_time(value: str, meridiem: str) -> str:
        value = value if ":" in value else f"{value}:00"
        return f"{value}{meridiem.upper()}"
