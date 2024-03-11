from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.google_url import extract_google_position
from locations.hours import DAYS_NL, OpeningHours, sanitise_day
from locations.items import Feature


class HemaSpider(Spider):
    name = "hema"
    item_attributes = {"brand": "HEMA", "brand_wikidata": "Q903805"}
    start_urls = [
        "https://www.hema.nl/on/demandware.store/Sites-HemaNL-Site/nl_NL/Stores-Load",
        "https://www.hema.com/on/demandware.store/Sites-HemaFR-Site/fr_FR/Stores-Load",
        "https://www.hema.com/on/demandware.store/Sites-HemaBE-Site/nl_BE/Stores-Load",
        # "https://www.hema.com/on/demandware.store/Sites-HemaBE-Site/fr_BE/Stores-Load",
        "https://www.hema.com/on/demandware.store/Sites-HemaDE-Site/de_DE/Stores-Load",
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//li[contains(@class, "store")]'):
            item = Feature()
            item["ref"] = location.xpath('.//input[@name="stores"]/@value').get()
            item["branch"] = location.xpath(".//h4/text()").get()
            item["street_address"], item["postcode"], item["city"], *_ = location.xpath(
                './/div[@class="store-info-main store-info js-selected-store-info"]/span/span/text()'
            ).getall()
            item["phone"] = response.xpath('.//a[@class="store-info-phone"]/text()').get()
            extract_google_position(item, location)

            item["opening_hours"] = OpeningHours()
            for rule in location.xpath(
                './/ul[@class="selected-store-opening-hours js-selected-store-opening-hours"]/li'
            ):
                if day := sanitise_day(rule.xpath('span[@class="day"]/text()').get(), DAYS_NL):
                    times = rule.xpath('span[@class="time"]/text()').get().strip()
                    if times == "gesloten":
                        continue
                    item["opening_hours"].add_range(day, *times.split(" - "))

            yield item

        if url := response.xpath('//a[@class="show-more js-show-more-stores"]/@href').get():
            yield response.follow(url)
