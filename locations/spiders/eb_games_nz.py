from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class EBGamesNZSpider(SitemapSpider, StructuredDataSpider):
    name = "eb_games_nz"
    item_attributes = {"brand": "EB Games", "brand_wikidata": "Q4993686"}
    sitemap_urls = ["https://www.ebgames.co.nz/sitemap-stores.xml"]
    sitemap_rules = [(r"\/store\/\w+$", "parse_sd")]
    wanted_types = ["Store"]
