from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class KeyBankSpider(SitemapSpider, StructuredDataSpider):
    name = "keybank"
    item_attributes = {"brand": "KeyBank", "brand_wikidata": "Q1740314"}
    sitemap_urls = ["https://www.key.com/about/seo.sitemap-locator.xml"]
    sitemap_rules = [(r"locations/.*/.*/.*/.*", "parse_sd")]
    time_format = "%H:%M:%S"

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = response.css("h1.address__title::text").get()
        yield item
