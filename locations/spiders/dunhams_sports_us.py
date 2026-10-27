import json
import re
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse

import scrapy
from scrapy import Spider
from scrapy.http import Response

from locations.hours import OpeningHours
from locations.items import Feature


class DunhamsSportsUSSpider(Spider):
    name = "dunhams_sports_us"
    item_attributes = {"brand": "Dunham's Sports", "brand_wikidata": "Q5315238"}
    allowed_domains = ["www.dunhamssports.com"]
    start_urls = ["https://www.dunhamssports.com/store-locator"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for city_id in response.xpath('//*[@name="store-locator-store-id"]//@value').getall():
            if city_id:
                yield scrapy.Request(
                    url=f"https://www.dunhamssports.com/find-stores/?storeId={city_id}", callback=self.parse_details
                )

    def parse_details(self, response):
        for lat_lon_data in json.loads(response.xpath('//*[@id="coordinates-data"]/@value').get()):
            location_id = lat_lon_data["num"]
            for location in response.xpath(f'//*[@id="map-info-{location_id}"]'):
                item = Feature()
                item["lat"] = lat_lon_data["lat"]
                item["lon"] = lat_lon_data["lng"]
                lines = [
                    (location.xpath(f'.//*[@class="fs-13px mb-2 fw-medium"]/div[{i}]/text()').get() or "").strip()
                    for i in (1, 2)
                ]
                item["branch"], item["street_address"] = self.split_address_lines(lines)
                city, state, postcode = (
                    (location.xpath(f'.//*[@class="fs-13px mb-2 fw-medium"]//span[{i}]/text()').get() or "")
                    .strip()
                    .rstrip(",.")
                    .strip()
                    for i in (1, 2, 3)
                )
                item["city"], item["postcode"] = city or None, postcode or None
                item["phone"] = location.xpath('.//*[contains(@href,"tel:")]/text()').get()
                item["ref"] = item["website"] = urljoin(
                    "https://www.dunhamssports.com/", location.xpath(".//span//@href").get().replace(" ", "")
                )
                item["state"] = state or parse_qs(urlparse(item["website"]).query).get("state", [None])[0]
                try:
                    oh = OpeningHours()
                    for day_time in location.xpath('.//*[@class="store-hours-table fs-13px mb-2"]//tr'):
                        oh.add_ranges_from_string("".join(day_time.xpath(".//td//text()").getall()))
                    item["opening_hours"] = oh
                except:
                    pass
                yield item

    @staticmethod
    def split_address_lines(lines: list[str]) -> tuple[str | None, str | None]:
        """Return (branch, street) from the two lines above the city line.

        The first line is a shopping-centre name or the street; the second is
        the street, a unit ("Suite B"), a centre name, or empty.
        """
        unit_line = next((line for line in lines if UNIT.match(line)), None)
        unit, centre = unit_line, None
        if unit_line and (numbered := NUMBERED_UNIT.match(unit_line)):
            unit, centre = numbered.groups()  # "#74 Colony Square Mall"
        street = next((line for line in lines if STREET.match(line)), None)
        if street is None:
            # An unnumbered street: the second line, as before, unless it is a unit; else a
            # first line that doesn't name a centre ("Highway 50 W", not "Cross Creek Mall").
            if lines[1] and lines[1] != unit_line:
                street = lines[1]
            elif lines[0] and lines[0] != unit_line and not CENTRE.search(lines[0]):
                street = lines[0]
        branch = next((line for line in lines if line and line not in (street, unit_line)), centre)
        return branch, ", ".join(filter(None, [street, unit])) or None


STREET = re.compile(r"^[A-Z]?-?\d")
UNIT = re.compile(r"^\(?(?:(?:suite|ste|unit|space|room)\b|#)", re.IGNORECASE)
# A "#" unit followed by a shopping-centre name: "#74 Colony Square Mall".
NUMBERED_UNIT = re.compile(r"^(#\s*[\w-]+)\s+(\D.*)$")
CENTRE = re.compile(
    r"\b(?:mall|plaza|cent(?:er|re)|square|shopping|shoppes|crossing|commons|marketplace)\b", re.IGNORECASE
)
