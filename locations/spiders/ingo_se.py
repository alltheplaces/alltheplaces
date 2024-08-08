from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.structured_data_spider import StructuredDataSpider


class IngoSESpider(SitemapSpider, StructuredDataSpider):
    name = "ingo_se"
    item_attributes = {"brand": "Ingo", "brand_wikidata": "Q17048617"}
    sitemap_urls = ["https://www.ingo.se/stations/sitemap.xml"]
    wanted_types = ["GasStation"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        extract_google_position(item, response)
        apply_category(Categories.FUEL_STATION, item)

        yield item
