from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.nandos import NANDOS_SHARED_ATTRIBUTES
from locations.structured_data_spider import StructuredDataSpider

NINO_NANDOS = {"name": "Nino Nando's", "brand": "Nino Nando's", "brand_wikidata": "Q111753283"}


class NandosGBIESpider(SitemapSpider, StructuredDataSpider):
    name = "nandos_gb_ie"
    item_attributes = NANDOS_SHARED_ATTRIBUTES
    sitemap_urls = ["https://www.nandos.co.uk/robots.txt"]
    sitemap_rules = [(".co.uk/restaurants/", "parse")]
    wanted_types = ["Restaurant"]
    skip_auto_cc_domain = True

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name")
        if "our Nino restaurant" in response.text:
            item.update(NINO_NANDOS)
            apply_category(Categories.FAST_FOOD, item)
        yield item
