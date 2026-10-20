from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider, clean_facebook


class AutovisionFRSpider(SitemapSpider, StructuredDataSpider):
    name = "autovision_fr"
    item_attributes = {"brand": "Autovision", "brand_wikidata": "Q64224842"}
    sitemap_urls = ["https://www.autovision.fr/centres-sitemap.xml"]
    wanted_types = ["AutomotiveBusiness"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if clean_facebook(item.get("facebook")) == "https://www.facebook.com/AutovisionOfficiel/":
            item["facebook"] = None

        apply_category(Categories.VEHICLE_INSPECTION, item)
        yield item
