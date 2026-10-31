import re
from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class ShakeShackSpider(CrawlSpider):
    name = "shake_shack"
    item_attributes = {"brand": "Shake Shack", "brand_wikidata": "Q1058722"}
    start_urls = ["https://shakeshack.com/locations"]
    rules = [Rule(LinkExtractor(allow=r"/node/\d+$"), callback="parse_location")]
    custom_settings = {"DOWNLOAD_DELAY": 2, "CONCURRENT_REQUESTS": 2}
    requires_proxy = True

    def parse_location(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["branch"] = response.xpath("normalize-space(//h1)").get()
        item["street_address"] = response.xpath(
            '//*[contains(@class, "field--name-field-address-line-1-ss2")]/text()'
        ).get()
        city_state = response.xpath(
            'normalize-space(//h2[contains(@class, "field--name-field-hero-description")])'
        ).get()
        item["city"], _, item["state"] = (part.strip() for part in city_state.partition(","))
        item["postcode"] = response.xpath(
            'normalize-space(//*[@id="location-info--left__address"]/text()[normalize-space()][last()])'
        ).re_first(r"(\d{5}(?:-\d{4})?)\s*$")
        item["country"] = "US"
        item["lat"] = response.xpath("//@data-lat").get()
        item["lon"] = response.xpath("//@data-lng").get()
        phone = response.xpath(
            '//*[@id="location-info--left__phone"]//div[contains(@class, "field__item")]/text()'
        ).get()
        if phone and not re.sub(r"\D", "", phone).endswith("5555555"):
            item["phone"] = phone

        item["opening_hours"] = OpeningHours()
        for day in response.xpath('//*[@id="location-info--middle__hours"]/div'):
            if hours := day.xpath('normalize-space(.//*[@class="location--hours"])').get():
                open_time, _, close_time = hours.partition("–")
                item["opening_hours"].add_range(
                    day.xpath('normalize-space(.//*[@class="location--weekend"])').get(),
                    open_time.strip(),
                    close_time.strip(),
                    "%I:%M %p",
                )

        apply_category(Categories.FAST_FOOD, item)
        yield item
