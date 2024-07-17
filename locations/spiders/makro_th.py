import scrapy

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature


class MakroTHSpider(scrapy.Spider):
    name = "makro_th"
    item_attributes = {"brand_wikidata": "Q704606"}
    start_urls = ["https://www.makro.co.th/th/contact-us-branch-makro/"]

    def parse(self, response):
        for i in range(1, 20):
            # There are 8 zones, but who knows if they will add more in the future
            zone_url = response.xpath(f'//li[@id="branch_zone{i}"]/a/@href').get()
            if zone_url:
                yield scrapy.Request(zone_url, self.parse_zone)
            else:
                break

    def parse_zone(self, response):
        store_links = response.xpath('//div[@id="accordion_branchprovince"]//a/@href').getall()
        for store_link in store_links:
            yield scrapy.Request(store_link, self.parse_store)

    def parse_store(self, response):
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["state"] = response.xpath(
            '//div[contains(@class, "contact-data-wrap")]/p[@class="txt-black txt-25"]/text()'
        ).get()
        item["addr_full"] = response.xpath(
            '//div[contains(@class, "contact-data-wrap")]/p[@class="txt-black txt-18 f-normal"]/text()'
        ).get()
        extract_google_position(item, response.xpath('//div[@id="mag-gg"]'))
        apply_category(Categories.SHOP_WHOLESALE, item)
        # TODO: phone
        yield item
