import re

from scrapy.spiders import SitemapSpider

from locations.items import Feature


class GoodyearSpider(SitemapSpider):
    name = "goodyear"
    item_attributes = {"brand": "Goodyear", "brand_wikidata": "Q620875"}
    allowed_domains = ["www.goodyear.eu"]
    sitemap_urls = ["https://www.goodyear.eu/robots.txt"]
    sitemap_follow = [r"/(?!ru_ru)[a-z]{2}_[a-z]{2}/consumer.dealers-sitemap.xml"]
    sitemap_rules = [(r"\/dealers\/\d+\/", "parse_store")]

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
