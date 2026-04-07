from copy import deepcopy

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.structured_data_spider import StructuredDataSpider


class BanquePopulaireFRSpider(SitemapSpider, StructuredDataSpider):
    name = "banque_populaire_fr"
    item_attributes = {"brand": "Banque Populaire", "brand_wikidata": "Q846647"}
    sitemap_urls = ["https://agences.banquepopulaire.fr/banque-assurance/sitemap-bp.xml"]
    sitemap_rules = [("-id", "parse_sd")]
    drop_attributes = {"image"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["website"] = response.url

        has_atm = bool(response.xpath('//*[contains(@class, "em-details__services-dab")]'))

        bank = deepcopy(item)
        apply_category(Categories.BANK, bank)
        apply_yes_no(Extras.ATM, bank, has_atm)
        yield bank

        if has_atm:
            atm = deepcopy(item)
            atm["ref"] += "-ATM"
            apply_category(Categories.ATM, atm)
            yield atm
