from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.spiders.central_england_cooperative import COOP_FUNERALCARE, set_operator
from locations.structured_data_spider import StructuredDataSpider

THE_COOPERATIVE_GROUP = {"brand": "The Co-operative Group", "brand_wikidata": "Q117202"}
THE_COOPERATIVE_GROUP_FOOD = {"brand": "Co-op Food", "brand_wikidata": "Q3277439"}


class TheCooperativeGroupSpider(SitemapSpider, StructuredDataSpider):
    name = "the_cooperative_group"
    sitemap_urls = [
        "https://www.coop.co.uk/store-finder/sitemap.xml",
        "https://www.coop.co.uk/funeralcare/funeral-directors/sitemap.xml",
    ]
    sitemap_rules = [
        ("/store-finder/", "parse_sd"),
        ("/funeralcare/funeral-directors/", "parse_sd"),
    ]
    wanted_types = ["ConvenienceStore", "LocalBusiness"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if ld_data["@type"] == "ConvenienceStore":
            item.update(THE_COOPERATIVE_GROUP_FOOD)
            apply_category(Categories.SHOP_CONVENIENCE, item)
        else:
            item.update(COOP_FUNERALCARE)
            apply_category(Categories.SHOP_FUNERAL_DIRECTORS, item)

        set_operator(THE_COOPERATIVE_GROUP, item)

        yield item
