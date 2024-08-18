from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class WaynesCoffeeSpider(SitemapSpider, StructuredDataSpider):
    name = "waynes_coffee"
    sitemap_urls = ["https://www.waynescoffee.se/sitemap.xml", "https://www.waynescoffee.jo/sitemap.xml"]
    sitemap_rules = [(r"/kafe/[\w-]+/", "parse_sd")]
    item_attributes = {"brand": "Waynes Coffee", "brand_wikidata": "Q10397787"}
    wanted_types = ["CafeOrCoffeeShop"]
    no_refs = True
