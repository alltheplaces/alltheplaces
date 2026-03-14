from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

ICA_KVANTUM = {"name": "ICA Kvantum", "brand": "ICA Kvantum", "brand_wikidata": "Q1663776"}
ICA_NARA = {"name": "ICA Nära", "brand": "ICA Nära", "brand_wikidata": "Q1663776"}
ICA_SUPERMARKET = {"name": "ICA Supermarket", "brand": "ICA Supermarket", "brand_wikidata": "Q1663776"}
ICA_MAXI = {"name": "Maxi ICA Stormarknad", "brand": "Maxi ICA Stormarknad", "brand_wikidata": "Q1663776"}


class IcaSESpider(SitemapSpider, StructuredDataSpider):
    name = "ica_se"
    sitemap_urls = ["https://www.ica.se/butiker/sitemap.xml"]
    sitemap_rules = [(r"/butiker/[^/]+/[^/]+/[^/]+-\d+/$", "parse_sd")]
    wanted_types = ["GroceryStore"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        if "/butiker/kvantum/" in response.url:
            item["branch"] = item.pop("name").removeprefix(ICA_KVANTUM["name"]).strip()
            item.update(ICA_KVANTUM)
        elif "/butiker/nara/" in response.url:
            item["branch"] = item.pop("name").removeprefix(ICA_NARA["name"]).strip()
            item.update(ICA_NARA)
        elif "/butiker/supermarket/" in response.url:
            item["branch"] = item.pop("name").removeprefix(ICA_SUPERMARKET["name"]).strip()
            item.update(ICA_SUPERMARKET)
        elif "/butiker/maxi/" in response.url:
            item["branch"] = item.pop("name").removeprefix(ICA_MAXI["name"]).strip()
            item.update(ICA_MAXI)
        else:
            self.logger.error("Unknown brand: {}".format(response.url))

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
