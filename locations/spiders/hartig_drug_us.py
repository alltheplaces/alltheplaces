import re
from typing import Any, Iterable

from parsel import Selector
from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class HartigDrugUSSpider(Spider):
    name = "hartig_drug_us"
    item_attributes = {"brand": "Hartig Drug", "brand_wikidata": "Q5674643"}
    allowed_domains = ["www.hartigdrug.com"]
    start_urls = ["https://www.hartigdrug.com/stores"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Request]:
        for row in response.xpath(
            '//div[contains(@class, "view-display-id-block_1")]/div[contains(@class, "view-content")]/table/tbody/tr'
        ):
            if (
                row.xpath('normalize-space(./td[contains(@class, "views-field-field-address")])').get()
                == "PERMANENTLY CLOSED"
            ):
                continue
            yield response.follow(
                row.xpath('./td[contains(@class, "views-field-path")]/a/@href').get(), callback=self.parse_location
            )

    def parse_location(self, response: Response) -> Iterable[Feature]:
        city_state_postcode = response.xpath(
            'normalize-space(//div[contains(@class, "field-name-field-address-two")])'
        ).get()
        if not (address_match := re.fullmatch(r"(.+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)", city_state_postcode)):
            return

        title = response.xpath('normalize-space(//h1[@id="page-title"])').get()
        item = Feature(
            ref=response.xpath(
                'normalize-space(//div[contains(@class, "field-name-field-store-number")]//div[contains(@class, "field-item")])'
            ).get(),
            branch=title.removeprefix("Hartig Drug").lstrip(" -"),
            street_address=response.xpath(
                'normalize-space(//div[contains(@class, "field-name-field-address")]//div[contains(@class, "field-item")])'
            ).get(),
            city=address_match.group(1),
            state=address_match.group(2),
            postcode=address_match.group(3),
            country="US",
            phone=response.xpath(
                'normalize-space(//div[contains(@class, "field-name-field-home-phone")]//div[contains(@class, "field-item")])'
            ).get(),
            website=response.url,
            opening_hours=self.parse_hours(response.xpath('//div[@id="store-hours"]')),
        )

        if pharmacy_hours := self.parse_hours(response.xpath('//div[@id="pharmacy-hours"]')):
            item["extras"]["opening_hours:pharmacy"] = pharmacy_hours.as_opening_hours()

        apply_category(Categories.PHARMACY, item)
        yield item

    @staticmethod
    def parse_hours(hours_element: Selector) -> OpeningHours:
        hours_text = " ".join(hours_element.xpath(".//p//text()").getall())
        hours_text = re.sub(r"\s+", " ", hours_text).replace("M-F", "Mon-Fri")
        hours_text = re.sub(r"\bM:", "Mon:", hours_text)
        hours = OpeningHours()
        hours.add_ranges_from_string(hours_text)
        return hours
