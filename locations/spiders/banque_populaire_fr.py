from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.structured_data_spider import StructuredDataSpider


class BanquePopulaireFRSpider(SitemapSpider, StructuredDataSpider):
    name = "banque_populaire_fr"
    item_attributes = {"brand": "Banque Populaire", "brand_wikidata": "Q846647"}
    sitemap_urls = ["https://agences.banquepopulaire.fr/sitemap_pois.xml"]
    sitemap_rules = [(r"https://agences.banquepopulaire.fr/fr/agence/[^/]+$", "parse_sd")]
    drop_attributes = {"image"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name")
        item["website"] = response.url

        apply_category(Categories.BANK, item)
        apply_yes_no(
            Extras.ATM,
            item,
            "Distributeur automatique de billets"
            in response.xpath('//*[contains(@data-testid,"service-card")]//text()').getall(),
        )
        yield item
