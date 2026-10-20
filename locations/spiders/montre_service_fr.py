from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class MontreServiceFRSpider(CrawlSpider, StructuredDataSpider):
    name = "montre_service_fr"
    item_attributes = {
        "brand": "Montre Service",
        "brand_wikidata": "Q141155781",
    }
    allowed_domains = ["montreservice.fr"]
    start_urls = ["https://montreservice.fr/fr/boutiques"]

    rules = [
        Rule(
            LinkExtractor(allow=r"/boutiques/.*"),
            "parse_sd",
            follow=True,
        ),
    ]

    drop_attributes = {"facebook"}

    def post_process_item(self, item, response, ld_data):
        if not item.get("street_address"):  # Shops without a street address are invalid.
            return

        item["branch"] = (item.pop("name", "") or "").removeprefix("Horlogerie à ").removesuffix(" : MONTRE SERVICE")
        if "MONTRE SERVICE" in item["branch"]:  # the name format is not cleaned properly
            item["branch"] = None

        apply_category(Categories.SHOP_WATCHES, item)
        yield item
