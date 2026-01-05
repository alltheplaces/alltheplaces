from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class CaisseDEpargneFRSpider(SitemapSpider, StructuredDataSpider):
    name = "caisse_d_epargne_fr"
    item_attributes = {"brand": "Caisse d'Épargne", "brand_wikidata": "Q1547738"}
    sitemap_urls = ["https://www.agences.caisse-epargne.fr/banque-assurance/agences/sitemap.xml"]
    sitemap_follow = ["/banque-assurance/"]
    sitemap_rules = [("-id", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["image"] = None
        item["name"] = None
        if "Distributeur automatique de billets" in response.text:
            atm = item.deepcopy()
            atm["ref"] += "-ATM"
            atm["opening_hours"] = None
            apply_category(Categories.ATM, atm)
            yield atm
        apply_category(Categories.BANK, item)
        yield item
