import chompjs
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser


class BinnysSpider(SitemapSpider):
    name = "binnys"
    item_attributes = {"brand": "Binny's Beverage Depot", "brand_wikidata": "Q30687714"}
    allowed_domains = ["binnys.com"]
    sitemap_urls = ["https://www.binnys.com/robots.txt"]
    sitemap_rules = [(r"/store-locator/", "parse")]

    def parse(self, response):
        if script := response.xpath('//script/text()[contains(.,"var serverSideViewModel")]').get():
            data = chompjs.parse_js_object(script)
            item = DictParser.parse(data)
            item["branch"] = item.pop("name")
            yield item
