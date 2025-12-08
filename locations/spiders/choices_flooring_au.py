from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class ChoicesFlooringAUSpider(SitemapSpider, StructuredDataSpider):
    name = "choices_flooring_au"
    item_attributes = {
        "brand": "Choices Flooring",
        "brand_wikidata": "Q117155570",
        "extras": Categories.SHOP_FLOORING.value,
    }
    sitemap_urls = ["https://www.choicesflooring.com.au/sitemap-xml"]
    sitemap_rules = [("/stores", "parse_sd")]
