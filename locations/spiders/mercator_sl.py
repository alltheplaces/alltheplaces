from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class MercatorSLSpider(SitemapSpider, StructuredDataSpider):
    name = "mercator_sl"
    item_attributes = {"brand": "Mercator", "brand_wikidata": "Q738412"}
    allowed_domains = ["www.mercator.si"]
    sitemap_urls = ["https://www.mercator.si/sitemap.xml/sitemap/Store/1", "https://www.mercator.si/sitemap.xml/sitemap/Store/2"]
    sitemap_rules = [
        (r"^https:\/\/www\.mercator\.si\/prodajna-.*/.*/$", "parse_sd"),
    ]
    wanted_types = ["LocalBusiness"]
