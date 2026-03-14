from scrapy import Request, Spider

from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class ToysrusBWNAZAZMSpider(Spider):
    name = "toysrus_bw_na_za_zm"
    allowed_domains = ["www.toysrus.co.za"]
    start_urls = ["https://www.toysrus.co.za/find-a-store"]
    item_attributes = {
        "brand": "Toys R Us",
        "brand_wikidata": "Q130461516",
    }
    skip_auto_cc_domain = True

    def parse(self, response):
        for url in response.xpath('.//a[@class="product-item-link"]/@href').getall():
            yield Request(url=url, callback=self.parse_store)

    def parse_store(self, response):
        item = Feature()
        item["ref"] = response.url
        item["website"] = response.url
        item["branch"] = response.xpath(".//h1/span/text()").get()
        item["addr_full"] = clean_address(response.xpath('.//div[@class="address-line"]/text()').get())
        item["phone"] = response.xpath('.//a[@class="phone-number"]/@href').get()
        extract_google_position(item, response)

        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(response.xpath('string(.//div[@class="working-times "])').get())
        yield item
