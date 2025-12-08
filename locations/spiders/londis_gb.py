import scrapy

from locations.categories import Categories
from locations.open_graph_spider import OpenGraphSpider


class LondisGBSpider(scrapy.spiders.SitemapSpider, OpenGraphSpider):
    name = "londis_gb"
    item_attributes = {"brand": "Londis", "brand_wikidata": "Q21008564", "extras": Categories.SHOP_CONVENIENCE.value}
    allowed_domains = ["londis.co.uk"]
    sitemap_urls = ["https://www.londis.co.uk/sitemap.xml"]
    sitemap_rules = [("/our-stores/", "parse")]
