from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BassProShopsSpider(SitemapSpider, StructuredDataSpider):
    name = "bass_pro_shops"
    item_attributes = {"brand": "Bass Pro Shops", "brand_wikidata": "Q4867953"}
    allowed_domains = ["stores.basspro.com"]
    sitemap_urls = ["https://stores.basspro.com/sitemap.xml"]
    sitemap_rules = [(r"https://stores.basspro.com/.+/.+/.+/.+.html$", "parse_sd")]
