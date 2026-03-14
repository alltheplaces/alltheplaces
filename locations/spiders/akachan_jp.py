from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class AkachanJPSpider(SitemapSpider, StructuredDataSpider):
    name = "akachan_jp"
    item_attributes = {"brand_wikidata": "Q11257015"}
    allowed_domains = ["stores.akachan.jp"]
    sitemap_urls = ["https://stores.akachan.jp/sitemap.xml"]
    sitemap_rules = [(r"stores\.akachan\.jp/\d+$", "parse_sd")]
    drop_attributes = {"image"}
