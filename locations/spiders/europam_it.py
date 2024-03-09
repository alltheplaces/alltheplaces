from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.structured_data_spider import StructuredDataSpider


class EuropamITSpider(SitemapSpider, StructuredDataSpider):
    name = "europam_it"
    item_attributes = {"brand": "Europam", "brand_wikidata": "Q115268198"}
    sitemap_urls = ["https://europam.it/robots.txt"]
    sitemap_rules = [("/stazioni-di-servizio/mappa-distributori/", "parse")]
    wanted_types = ["GasStation"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = None  # Address
        extract_google_position(item, response)
        apply_category(Categories.FUEL_STATION, item)

        yield item
