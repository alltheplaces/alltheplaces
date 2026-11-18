import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.google_url import extract_google_position
from locations.hours import DAYS_DE, DAYS_FR, DAYS_NL, OpeningHours, sanitise_day
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
    DAYS = {"NL": DAYS_NL, "BE": DAYS_NL, "FR": DAYS_FR, "DE": DAYS_DE}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        country = response.url.split("/Stores-Load", 1)[0].split("_")[-1]
        for location in response.xpath('//li[contains(@class, "store")]'):
            item = Feature()
            item["ref"] = location.xpath('.//input[contains(@class, "js-store-select")]/@value').get()
            info = location.xpath('.//div[contains(@class, "js-selected-store-info")]')[0]
            item["branch"] = info.xpath("./h4/text()").get()
            item["street_address"] = info.xpath('.//span[@class="js-store-address"]/text()').get()
            item["postcode"], item["city"] = info.xpath('.//span[@class="row-break"]/span/text()').getall()
            item["city"] = re.sub(r"\s*\([A-Z]{2}\)$", "", item["city"])
            item["phone"] = info.xpath('.//a[@class="store-info-phone"]/text()').get()
            extract_google_position(item, location)
            item["country"] = country

            item["opening_hours"] = OpeningHours()
            for rule in location.xpath(
                './/ul[@class="selected-store-opening-hours js-selected-store-opening-hours"]/li'
            ):
                if day := sanitise_day(rule.xpath('span[@class="day"]/text()').get(), self.DAYS[country]):
                    times = rule.xpath('span[@class="time"]/text()').get().strip()
                    if " - " not in times:  # closed
                        item["opening_hours"].set_closed(day)
                    else:
                        item["opening_hours"].add_range(day, *times.split(" - "))

            yield item

        if url := response.xpath('//a[@class="show-more js-show-more-stores"]/@href').get():
            yield response.follow(url)
