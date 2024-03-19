from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class ChicosSpider(SitemapSpider, StructuredDataSpider):
    name = "chicos"
    item_attributes = {"brand": "Chico's", "brand_wikidata": "Q5096393", "extras": Categories.SHOP_CLOTHES.value}
    sitemap_urls = ["https://www.chicos.com/web_assets/sitemaps/SiteMap.xml"]
    sitemap_rules = [("/locations/", "parse_sd")]
