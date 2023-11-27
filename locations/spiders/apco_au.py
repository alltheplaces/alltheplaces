from scrapy import Spider

from locations.items import Feature


class APCOAUSpider(Spider):
    name = "apco_au"
    item_attributes = {"brand": "APCO", "brand_wikidata": ""}
    allowed_domains = ["www.apco.com.au"]
    start_urls = ["https://www.apco.com.au/locations"]

    def parse(self, response):
        for location_html in response.xpath('//div[contains(@class, "location") and @data-index]'):
            if "Support Office" in location_html.xpath('.//h2/text()').get().title():
                continue
            properties = {
                "ref": location_html.xpath('.//@data-index').get(),
                "name": location_html.xpath('.//h2/text()').get(),
                "street_address": location_html.xpath('.//span[contains(@class, "address")]/text()').get(),
                "city": location_html.xpath('.//span[contains(@class, "suburb")]/text()').get(),
                "postcode": location_html.xpath('.//span[contains(@class, "postcode")]/text()').get(),
                "state": location_html.xpath('.//p[contains(@class, "full-address")]/text()').replace(",", "").strip(),
                "phone": location_html.xpath('.//a[contains(@class, "phone")]/@href').get().replace("tel:", ""),
            }
            yield Feature(**properties)
