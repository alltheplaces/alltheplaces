from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BlackRedWhitePLSpider(SitemapSpider, StructuredDataSpider):
    name = "black_red_white_pl"
    item_attributes = {"brand": "Black Red White", "brand_wikidata": "Q4921546"}
    sitemap_urls = ["https://www.brw.pl/sitemap/salony.xml"]
    sitemap_follow = ["salony"]
    no_refs = True
