from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class BikeTotaalNLSpider(SitemapSpider, StructuredDataSpider):
    name = "bike_totaal_nl"
    item_attributes = {"brand": "Bike Totaal", "brand_wikidata": "Q123536506", "extras": Categories.SHOP_BICYCLE.value}
    allowed_domains = ["www.biketotaal.nl"]
    sitemap_urls = ["https://www.biketotaal.nl/sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/www\.biketotaal\.nl\/fietsenwinkel\/bike-totaal-[^/]+$", "parse_sd")]

    def post_process_item(self, item, response, ld_data):
        item.pop("facebook", None)
        yield item
