import re
from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature


class PerrysSteakhouseAndGrilleUSSpider(Spider):
    name = "perrys_steakhouse_and_grille_us"
    item_attributes = {"brand": "Perry's Steakhouse & Grille"}
    allowed_domains = ["perryssteakhouse.com"]
    start_urls = ["https://perryssteakhouse.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Request]:
        for location in response.xpath(
            '//a[contains(concat(" ", normalize-space(@class), " "), " loc-spacer ") '
            'and not(contains(concat(" ", normalize-space(@class), " "), " coming "))]'
        ):
            address_lines = [line.strip() for line in location.xpath(".//address//text()").getall() if line.strip()]
            if not address_lines or not (
                address_match := re.fullmatch(r"(.+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)", address_lines[-1])
            ):
                continue

            yield response.follow(
                location.attrib["href"],
                callback=self.parse_location,
                cb_kwargs={
                    "branch": location.xpath("normalize-space(.//h5)").get(),
                    "street_address": ", ".join(address_lines[:-1]),
                    "city": address_match.group(1),
                    "state": address_match.group(2),
                    "postcode": address_match.group(3),
                },
            )

    def parse_location(
        self, response: Response, branch: str, street_address: str, city: str, state: str, postcode: str
    ) -> Iterable[Feature]:
        item = Feature(
            ref=response.url.rstrip("/").rsplit("/", 1)[-1],
            branch=branch,
            street_address=street_address,
            city=city,
            state=state,
            postcode=postcode,
            country="US",
            phone=response.xpath('(//div[@id="hours-location"]//a[starts-with(@href, "tel:")]/@href)[1]').get(),
            website=response.url,
        )

        hours = OpeningHours()
        for rule in response.xpath('//div[contains(@class, "covid-hours")]//p[contains(@class, "dine-in")]'):
            hours.add_ranges_from_string(re.sub(r"\([^)]*\)", " ", rule.xpath("string(.)").get()), days=DAYS_EN)
        item["opening_hours"] = hours

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "steak_house"
        yield item
