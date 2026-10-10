from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class SquareHabitatFRSpider(SitemapSpider, StructuredDataSpider):
    name = "square_habitat_fr"
    item_attributes = {
        "brand": "Square Habitat",
        "brand_wikidata": "Q64027038",
    }
    sitemap_urls = ["https://www.squarehabitat.fr/sitemap-agences-immo.xml"]
    sitemap_rules = [
        (r"/agence/[^/]+", "parse"),
    ]
    wanted_types = ["RealEstateAgent"]
    time_format = "%H:%M:%S"

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.OFFICE_ESTATE_AGENT, item)
        item["branch"] = item.pop("name", "").removesuffix(" Square Habitat")

        yield item
