from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class BikeTotaalNLSpider(SitemapSpider, StructuredDataSpider):
    name = "bike_totaal_nl"
    item_attributes = {"brand": "Bike Totaal", "brand_wikidata": "Q123536506"}
    allowed_domains = ["www.biketotaal.nl"]
    sitemap_urls = ["https://www.biketotaal.nl/sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/www\.biketotaal\.nl\/fietsenwinkel\/bike-totaal-[^/]+$", "parse_sd")]

    def post_process_item(self, item, response, ld_data):
        item.pop("facebook", None)
        apply_category(Categories.SHOP_BICYCLE, item)
        yield item
