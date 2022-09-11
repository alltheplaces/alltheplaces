from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser


class BiaggisSpider(SitemapSpider):
    name = "biaggis"
    item_attributes = {"brand": "Biaggis", "brand_wikidata": "Q113754664"}
    allowed_domains = ["biaggis.com"]
    download_delay = 2
    sitemap_urls = ["https://biaggis.com/location-sitemap.xml"]
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
    }

    def parse(self, response):
        item = LinkedDataParser.parse(response, "LocalBusiness")

        if item is None:
            return

        yield item
