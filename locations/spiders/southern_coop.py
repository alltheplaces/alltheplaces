from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.spiders.central_england_cooperative import COOP_FOOD, set_operator
from locations.structured_data_spider import StructuredDataSpider

SOUTHERN_COOP = {"brand": "The Southern Co-operative", "brand_wikidata": "Q7569773"}


class SouthernCoopSpider(SitemapSpider, StructuredDataSpider):
    name = "southern_coop"
    sitemap_urls = ["https://stores.southern.coop/robots.txt"]
    sitemap_rules = [(r"\.coop\/[-\w]+\/[-\w]+\/[-\w]+\.html$", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        set_operator(SOUTHERN_COOP, item)
        item.update(COOP_FOOD)
        apply_category(Categories.SHOP_CONVENIENCE, item)

        yield item
