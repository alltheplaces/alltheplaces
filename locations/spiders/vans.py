import json

import scrapy
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser


class VansSpider(SitemapSpider):
    name = "vans"
    item_attributes = {"brand": "Vans", "brand_wikidata": "Q1135366"}
    allowed_domains = ["vans.com"]
    sitemap_urls = ["https://www.vans.com/sitemaps/store-locations.xml"]
    sitemap_rules = [("", "parse")]

    def parse(self, response):
        data = response.xpath('//script[text()[contains(.,"LocalBusiness")]]/text()')
        # page 01
        if data:
            for store in data:
                data_json = json.loads(store.get())
                item = DictParser.parse(data_json)
                item["ref"] = data_json.get("url")
                item["name"] = data_json.get("@name")
                yield item

        # page 02
        else:
            urls = response.xpath('//div[@class="itemlist"]/a/@href')
            for url in urls:
                yield scrapy.Request(url=response.urljoin(url.get()), callback=self.parse)
