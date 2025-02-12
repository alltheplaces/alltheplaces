from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class AuntieAnnesSpider(SitemapSpider, StructuredDataSpider):
    name = "auntie_annes"
    item_attributes = {"brand": "Auntie Anne's", "brand_wikidata": "Q4822010"}
    allowed_domains = ["auntieannes.com"]
    sitemap_urls = ["https://locations.auntieannes.com/robots.txt"]
    sitemap_rules = [(r"https://locations\.auntieannes\.com/\w\w/[-.\w]+/[-–\w]+$", "parse_sd")]
    drop_attributes = {"image"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = response.xpath('//meta[@property="og:title"]/@content').get().split(" | ")[0]
        yield item
