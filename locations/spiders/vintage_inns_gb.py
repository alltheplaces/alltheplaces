from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class VintageInnsGBSpider(SitemapSpider, StructuredDataSpider):
    name = "vintage_inns_gb"
    item_attributes = {"brand": "Vintage Inns", "brand_wikidata": "Q87067899"}
    sitemap_urls = ["https://www.vintageinn.co.uk/sitemap.xml"]
    sitemap_rules = [(r"/restaurants/[a-z-]+/[a-z-]+$", "parse_sd")]
    search_for_twitter = False
