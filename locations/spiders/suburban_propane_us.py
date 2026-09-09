from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.structured_data_spider import StructuredDataSpider


class SuburbanPropaneUSSpider(SitemapSpider, StructuredDataSpider):
    name = "suburban_propane_us"
    item_attributes = {"brand": "Suburban Propane", "brand_wikidata": "Q120122434"}
    sitemap_urls = ["https://www.suburbanpropane.com/locations-sitemap.xml"]
    sitemap_rules = [(r"/locations/[^/]+/$", "parse_sd")]
    # Times in openingHoursSpecification include seconds, e.g. "08:00:00"
    time_format = "%H:%M:%S"

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.SHOP_GAS, item)
        apply_yes_no(Fuel.LPG, item, True)
        yield item
