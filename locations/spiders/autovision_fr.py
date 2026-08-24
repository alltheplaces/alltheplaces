from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider, clean_facebook
from locations.categories import Categories, apply_category


class AutovisionFRSpider(SitemapSpider, StructuredDataSpider):
    name = "autovision_fr"
    item_attributes = {
        "brand": "Autovision",
        "brand_wikidata": "Q64224842",
    }
    sitemap_urls = ["https://www.autovision.fr/centres-sitemap.xml"]
    sitemap_rules = [(r"/", "parse_sd")]
    wanted_types = ["AutomotiveBusiness"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.VEHICLE_INSPECTION, item)
        item["branch"] = item.pop("name", "")

        if(clean_facebook(item.get("facebook")) == "https://www.facebook.com/AutovisionOfficiel/"):
            item["facebook"] = None

        yield item
