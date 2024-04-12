from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class ChampsSportsUSSpider(SitemapSpider, StructuredDataSpider):
    name = "champs_sports_us"
    item_attributes = {"brand": "Champs Sports", "brand_wikidata": "Q2955924"}
    sitemap_urls = ["https://stores.champssports.com/sitemap.xml"]
    sitemap_rules = [(r".html$", "parse_sd")]
    wanted_types = ["ShoeStore"]
    drop_attributes = {"name"}
