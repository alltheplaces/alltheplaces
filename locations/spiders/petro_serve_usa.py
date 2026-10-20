import re
from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature

TIME_PATTERN = re.compile(r"(\d{1,2})(?::(\d{2}))?\s*([ap])\.?\s*m\.?", re.IGNORECASE)


def normalise_time(text: str) -> str | None:
    if m := TIME_PATTERN.search(text):
        hour, minute, am_pm = m.groups()
        return f"{hour}:{minute or '00'} {am_pm.upper()}M"
    return None


class PetroServeUsaSpider(scrapy.Spider):
    name = "petro_serve_usa"
    item_attributes = {"brand": "Petro Serve USA", "country": "US"}
    allowed_domains = ["www.petroserveusa.com"]
    start_urls = ["https://www.petroserveusa.com/locations"]
    # The site's ASP.NET backend throws when no Referer header is present, returning a 500
    # response even though a normal, fully-rendered page follows the Referer-less request.
    handle_httpstatus_list = [500]

    def start_requests(self):
        yield scrapy.Request(url=self.start_urls[0], headers={"Referer": self.start_urls[0]}, callback=self.parse)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for href in response.xpath('//a[starts-with(@href, "/location/")]/@href').getall():
            if href == "/location/5":
                # Corporate office, not a retail/travel-centre location.
                continue
            yield scrapy.Request(
                url=response.urljoin(href),
                headers={"Referer": response.url},
                callback=self.parse_location,
            )

    def parse_location(self, response: Response) -> Any:
        ref = response.url.rstrip("/").rsplit("/", 1)[-1]

        address_lines = response.xpath('//h1[@itemprop="headline name"]/following-sibling::p[1]//text()').getall()
        address_lines = [line.strip() for line in address_lines if line.strip()]
        if len(address_lines) < 2:
            self.logger.error(f"Could not parse address for {response.url}")
            return
        street_address = address_lines[0]
        city_state_zip = address_lines[1]
        m = re.match(r"^(.*),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$", city_state_zip)

        item = Feature()
        item["ref"] = ref
        item["website"] = response.url
        item["branch"] = response.xpath('//h1[@itemprop="headline name"]/text()').get("").strip()
        item["name"] = self.item_attributes["brand"]

        if m:
            item["city"] = m.group(1)
            item["state"] = m.group(2)
            item["postcode"] = m.group(3)
            item["street_address"] = street_address
        else:
            item["addr_full"] = f"{street_address}, {city_state_zip}"

        phone = response.xpath('//p[starts-with(normalize-space(.), "Phone:")]/text()').get()
        if phone:
            phone = phone.replace("Phone:", "").strip()
            if phone:
                item["phone"] = phone

        item["opening_hours"] = self.parse_hours(response)

        apply_category(Categories.FUEL_STATION, item)

        yield item

    def parse_hours(self, response: Response) -> OpeningHours:
        oh = OpeningHours()
        for li in response.xpath('//h4[text()="Hours"]/following-sibling::ul[1]/li/text()').getall():
            if ":" not in li:
                continue
            day, hours = li.split(":", 1)
            day = day.strip()
            hours = hours.strip()
            if day not in DAYS_FULL:
                continue
            if "closed" in hours.lower():
                oh.set_closed(day)
                continue
            if "24 hr" in hours.lower():
                oh.add_range(day, "00:00", "23:59", "%H:%M")
                continue
            parts = re.split(r"[–—-]", hours, maxsplit=1)
            if len(parts) != 2:
                continue
            open_time = normalise_time(parts[0])
            close_time = normalise_time(parts[1])
            if open_time and close_time:
                oh.add_range(day, open_time, close_time, "%I:%M %p")
        return oh
