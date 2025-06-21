from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, DAYS_PL
from locations.items import Feature


class HygieiaPLSpider(Spider):
    name = "hygieia_pl"
    item_attributes = {"brand": "Hygieia", "brand_wikidata": "Q122906354"}
    allowed_domains = ["www.hygieia.pl"]
    start_urls = ["https://www.hygieia.pl/apteki.html"]

    def parse(self, response: Response) -> Iterable[Feature]:
        for store in response.xpath('//div[contains(@class, "media-body")]'):
            properties = {
                "ref": store.xpath('.//a[contains(@class, "link")]/@href').get().removeprefix("https://goo.gl/maps/"),
                "street_address": store.xpath('./h3/text()').get(),
                "city": store.xpath('./p[1]/text()').get(),
                "phone": store.xpath('.//i[contains(@class, "fa-phone")]/parent::p/text()').get(),
                "email": store.xpath('.//i[contains(@class, "fa-envelope")]/parent::p/text()').get(),
                "opening_hours": OpeningHours(),
            }
            hours_string = " ".join(store.xpath('.//i[contains(@class, "fa-clock")]/parent::p//text()').getall())
            properties["opening_hours"].add_ranges_from_string(hours_string, days=DAYS_PL)
            apply_category(Categories.PHARMACY, properties)
            properties["extras"]["ref:google:place_id"] = properties["ref"]
            yield Feature(**properties)
