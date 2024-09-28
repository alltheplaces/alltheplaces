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

        if item.get("image") and "agence-sg.jpg" in item["image"]:
            # Ignore generic image of a store that is used as a placeholder
            # when a location-specific image is not available.
            item.pop("image")

        yield item
