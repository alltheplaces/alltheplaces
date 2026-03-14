from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.central_england_cooperative import set_operator
from locations.structured_data_spider import StructuredDataSpider


class FairmontSpider(SitemapSpider, StructuredDataSpider):
    name = "fairmont"
    FAIRMONT = {"brand": "Fairmont", "brand_wikidata": "Q1393345"}
    sitemap_urls = ["https://www.fairmont.com/en.sitemap.xml"]
    sitemap_rules = [("/hotels/[^/]+/[^/]+html$", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        if item["name"].startswith("Fairmont"):
            item.update(self.FAIRMONT)
        elif item["name"].endswith("A Fairmont Managed Hotel"):
            set_operator(self.FAIRMONT, item)
            item["nsi_id"] = "N/A"

        apply_category(Categories.HOTEL, item)
        yield item
