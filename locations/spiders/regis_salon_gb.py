from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import extract_phone


class RegisSalonGBSpider(CrawlSpider):
    name = "regis_salon_gb"
    item_attributes = {
        "brand": "Regis Salon",
        "brand_wikidata": "Q110166032",
        "country": "GB",
    }
    allowed_domains = ["www.regissalons.co.uk"]
    start_urls = ["https://www.regissalons.co.uk/salon-locator"]
    download_delay = 4.0
    rules = [
        Rule(
            LinkExtractor(allow=r"https://www.regissalons.co.uk/salon-locator/[-\w]+/$"),
            callback="parse",
        )
    ]

    def parse(self, response):
        item = Feature()

        item["ref"] = item["website"] = response.url

        item["name"] = response.xpath('//h1[@class="page-title"]/span/text()').get()

        item["addr_full"] = response.xpath('//div[@class="amlocator-salon-left-address"]/p/text()').get()

        extract_google_position(item, response)
        extract_phone(item, response)

        oh = OpeningHours()
        for rule in response.xpath('//div[@class="amlocator-row"]'):
            day = rule.xpath('./span[@class="amlocator-cell -day"]/text()').get()
            time = rule.xpath('./span[@class="amlocator-cell -time"]/text()').get()

            if "closed" in time.lower():
                continue

            start_time, end_time = time.split(" - ")

            oh.add_range(day, start_time, end_time)

        item["opening_hours"] = oh.as_opening_hours()

        yield item
