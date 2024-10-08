import re
from hashlib import sha1

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class WinetimeUASpider(CrawlSpider):
    name = "winetime_ua"
    item_attributes = {"brand": "WINETIME", "brand_wikidata": "Q116698397"}
    allowed_domains = ["winetime.ua"]
    start_urls = ["https://winetime.ua/store/vinnytsia/"]
    rules = [
        Rule(
            LinkExtractor(
                allow=r"^https:\/\/winetime\.ua\/store\/[^/]+\/$",
                restrict_xpaths='//div[contains(@class, "city-choise")]/ul/li/a',
            ),
            callback="parse",
        )
    ]

    def parse_start_url(self, response):
        return self.parse(response)

    def parse(self, response):
        for location in response.xpath('//div[contains(@class, "city_content")]'):
            location_details = location.xpath('.//div[@class="block_content"]')
            properties = {
                "name": location_details.xpath("./h3/text()").get("").strip(),
                "lat": location.xpath('.//p[@class="latitude"]/text()').get("").strip(),
                "lon": location.xpath('.//p[@class="longitude"]/text()').get("").strip(),
                "street_address": re.sub(
                    r"Адреса\s+:\s+", "", location_details.xpath('./div[contains(text(), "Адреса")]/text()').get("")
                ).strip(),
                "city": response.xpath('//h1[@class="title"]/text()').get("").strip(),
                "phone": re.sub(
                    r"Телефон\s+:\s+", "", location_details.xpath('./div[contains(text(), "Телефон")]/text()').get("")
                ).strip(),
                "website": response.url,
                "opening_hours": OpeningHours(),
            }
            location_key = properties["street_address"] + properties["city"]
            properties["ref"] = sha1(location_key.encode("UTF-8")).hexdigest()
            properties["opening_hours"].add_days_range(
                DAYS,
                *map(
                    str.strip,
                    re.sub(
                        r"Час роботи\s+:\s+",
                        "",
                        location_details.xpath('./div[contains(text(), "Час роботи")]/text()').get(""),
                    ).split("-", 1),
                ),
                "%H:%M",
            )
            yield Feature(**properties)
