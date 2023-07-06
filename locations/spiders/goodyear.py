import re

from scrapy.spiders import SitemapSpider

from locations.items import Feature


class GoodyearEUSpider(SitemapSpider):
    name = "goodyear_eu"
    item_attributes = {"brand": "Goodyear", "brand_wikidata": "Q620875"}
    allowed_domains = ["www.goodyear.eu"]
    sitemap_urls = ["https://www.goodyear.eu/robots.txt"]
    sitemap_rules = [(r"", "parse_store")]

    def sitemap_filter(self, entries):
        for entry in entries:
            if "dealers" in entry["loc"]:
                yield entry

    def parse_store(self, response):
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["email"] = response.xpath('//ul[@class="dealer-ctas"]//a[contains(@href,"mailto")]//span/text()').get()
        item["phone"] = response.xpath('//span[@class="dealer-phone"]/text()').get()
        item["street_address"] = response.xpath('//p[@class="dealer-location"]/text()').get()
        item["lat"] = response.xpath("//@data-latlng").get().split(",")[0]
        item["lon"] = response.xpath("//@data-latlng").get().split(",")[1]
        item["country"] = re.findall(r"_[-\w]{2}", response.url)[0][1:].upper()
        yield item
