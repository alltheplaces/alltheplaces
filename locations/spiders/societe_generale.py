from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class SocieteGeneraleSpider(SitemapSpider, StructuredDataSpider):
    name = "societe_generale"
    item_attributes = {"brand_wikidata": "Q270363"}
    allowed_domains = ["societegenerale.com", "agences.sg.fr"]
    sitemap_urls = ["https://agences.sg.fr/banque-assurance/sitemap_agence_pois.xml"]
    sitemap_rules = [("", "parse_sd")]
    download_delay = 0.5

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Agence ").title()

        apply_category(Categories.BANK, item)

        yield item
