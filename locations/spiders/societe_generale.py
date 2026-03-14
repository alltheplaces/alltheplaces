from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class SocieteGeneraleSpider(SitemapSpider, StructuredDataSpider):
    name = "societe_generale"
    SG = {"name": "SG", "brand": "SG", "brand_wikidata": "Q270363"}
    CASH_SERVICE = {"brand": "Cash Service", "brand_wikidata": ""}
    allowed_domains = ["agences.sg.fr"]
    sitemap_urls = ["https://agences.sg.fr/banque-assurance/sitemap_index.xml"]
    sitemap_follow = [
        "particulier/sitemap_pois",
        "distributeur-automate/sitemap_pois",
    ]
    sitemap_rules = [(r"/.+-id(\d+)$", "parse_sd")]
    custom_settings = {"DOWNLOAD_TIMEOUT": 300}

    def pre_process_data(self, ld_data: dict, **kwargs):
        ld_data.pop("@id", None)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        if "Cash Service" in item["name"].title():
            item.update(self.CASH_SERVICE)
        else:
            item["branch"] = item.pop("name").title().removeprefix("Agence ")
            item.update(self.SG)

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
