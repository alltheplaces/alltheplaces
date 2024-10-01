from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class BanquePopulaireFRSpider(SitemapSpider, StructuredDataSpider):
    name = "banque_populaire_fr"
    item_attributes = {"brand": "Banque Populaire", "brand_wikidata": "Q846647"}
    sitemap_urls = ["https://agences.banquepopulaire.fr/banque-assurance/sitemap-bp.xml"]
    sitemap_rules = [("-id", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["website"] = response.url  # Bad url in linked data

        apply_category(Categories.BANK, item)

        yield item
    drop_attributes = {"image"}
