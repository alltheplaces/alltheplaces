from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature, set_closed
from locations.spiders.nandos import NANDOS_SHARED_ATTRIBUTES
from locations.structured_data_spider import StructuredDataSpider


class NandosGBIESpider(SitemapSpider, StructuredDataSpider):
    name = "nandos_gb_ie"
    item_attributes = NANDOS_SHARED_ATTRIBUTES
    sitemap_urls = ["https://www.nandos.co.uk/robots.txt"]
    sitemap_rules = [(r".co.uk/restaurants/([-\w]+)$", "parse")]
    wanted_types = ["Restaurant"]
    skip_auto_cc_domain = True

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name")

        if "Closed permanently" in response.text or "Closed for refurb" in response.text:
            set_closed(item)

        apply_category(Categories.RESTAURANT, item)

        yield item
