from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class HomebaseGBIESpider(SitemapSpider, StructuredDataSpider):
    name = "homebase_gb_ie"
    item_attributes = {"brand": "Homebase", "brand_wikidata": "Q9293447"}
    sitemap_urls = ["https://store.homebase.co.uk/robots.txt"]
    sitemap_rules = [(r"https:\/\/store\.homebase\.co\.uk\/[-.\w]+\/[-.\w]+$", "parse_sd")]
    skip_auto_cc_domain = True
    drop_attributes = {"image"}
