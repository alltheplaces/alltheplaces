from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class AmartFurnitureAUSpider(SitemapSpider, StructuredDataSpider):
    name = "amart_furniture_au"
    item_attributes = {"brand": "Amart Furniture", "brand_wikidata": "Q114119879"}
    sitemap_urls = ["https://www.amartfurniture.com.au/sitemap.xml"]
    sitemap_rules = [("/find/stores/", "parse_sd")]
