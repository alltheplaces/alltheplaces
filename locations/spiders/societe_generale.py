from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class SocieteGeneraleSpider(SitemapSpider, StructuredDataSpider):
    name = "societe_generale"
    item_attributes = {"name": "SG", "brand": "SG", "brand_wikidata": "Q270363"}
    allowed_domains = ["agences.sg.fr"]
    sitemap_urls = ["https://agences.sg.fr/banque-assurance/sitemap_index.xml"]
    sitemap_follow = [
        "particulier/sitemap_pois",
        "distributeur-automate/sitemap_pois",
    ]
    sitemap_rules = [(r"/.+-id(\d+)$", "parse_sd")]

    def pre_process_data(self, ld_data: dict, **kwargs):
        ld_data.pop("@id", None)

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Agence ").title()

        if "distributeur-automate" in response.url:
            item["ref"] += "_atm"
            apply_category(Categories.ATM, item)
        else:
            apply_category(Categories.BANK, item)

        if item.get("image") and "agence-sg.jpg" in item["image"]:
            # Ignore generic image of a store that is used as a placeholder
            # when a location-specific image is not available.
            item.pop("image")

        yield item
