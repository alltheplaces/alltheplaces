from scrapy.http import Request
from scrapy.spiders import Spider

from locations.google_url import extract_google_position
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class MiladysZASpider(Spider):
    name = "miladys_za"
    allowed_domains = ["www.miladys.com"]
    start_urls = ["https://www.miladys.com/storelocator"]
    item_attributes = {
        "brand": "Miladys",
        "brand_wikidata": "Q116619751",
    }

    def parse(self, response):
        for url in response.xpath('.//a[@class="store-info hidden-xs"]/@href').getall():
            yield Request(url=url, callback=self.parse_store)
        for url in response.xpath('.//a[@class="action  next"]/@href').getall():
            yield Request(url=url, callback=self.parse)

    def parse_store(self, response):
        item = Feature()
        item["ref"] = response.url
        item["website"] = response.url
        item["branch"] = response.xpath('.//h1[@class="page-title"]/span/text()').get().replace("Miladys", "").strip()
        item["addr_full"] = clean_address(response.xpath('.//div[@class="address-line"]/text()').get())
        item["phone"] = response.xpath('.//div[contains(@class,"phone-number")]/div/text()').get()
        extract_google_position(item, response)

        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(
            response.xpath('string(.//div[@class="shop-opening-times"])').get()
        )
        # Some places have no opening hours (for some days) so mysteriously return the current time for open and close
        for day in DAYS:
            if day in item["opening_hours"].days_closed:
                continue
            for h in sorted(item["opening_hours"].day_hours[day]):
                if h[0] == h[1]:
                    item["opening_hours"].day_hours[day].remove(h)

        yield item
