from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class FitXDESpider(SitemapSpider, StructuredDataSpider):
    name = "fitx_de"
    item_attributes = {"brand": "FitX", "brand_wikidata": "Q29031618"}
    sitemap_urls = ["https://www.fitx.de/studios/sitemap.xml"]
    wanted_types = ["ExerciseGym"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if ld_data.get("openingHours") == "Monday through Sunday, all day":
            item["opening_hours"] = "24/7"
        apply_category(Categories.GYM, item)
        item["branch"] = item["name"].replace("FitX Fitnessstudio ", "")
        yield item
