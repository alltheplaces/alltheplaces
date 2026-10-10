from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class MollyMaidUSSpider(SitemapSpider, StructuredDataSpider):
    name = "molly_maid_us"
    item_attributes = {"brand": "Molly Maid", "brand_wikidata": "Q6896624"}
    sitemap_urls = ["https://www.mollymaid.com/locations/wp-sitemap-posts-nbly_location-1.xml"]
    drop_attributes = {"image"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.CRAFT_CLEANING, item)
        yield item
