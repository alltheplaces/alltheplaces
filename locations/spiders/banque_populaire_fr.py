from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BanquePopulaireFRSpider(SitemapSpider, StructuredDataSpider):
    name = "banque_populaire_fr"
    item_attributes = {"brand": "Banque Populaire", "brand_wikidata": "Q846647"}
    sitemap_urls = ["https://agences.banquepopulaire.fr/robots.txt"]
    sitemap_rules = [(r"/fr/agence/[^/]+$", "parse")]
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
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
