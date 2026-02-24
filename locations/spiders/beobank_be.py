from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BeobankBESpider(SitemapSpider, StructuredDataSpider):
    name = "beobank_be"
    item_attributes = {"brand": "Beobank", "brand_wikidata": "Q14911971"}
    allowed_domains = ["www.beobank.be"]
    sitemap_urls = ["https://www.beobank.be/fr/sitemap.xml"]
    sitemap_rules = [
        (r"/nl/kantoor/vlaams-gewest/.+/\d+\.html$", "parse_sd"),
        (r"/fr/agence/region-wallonne/.+/\d+\.html$", "parse_sd"),
        (r"/fr/agence/region-de-bruxelles-capitale/.+/\d+\.html$", "parse_sd"),
    ]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = (
            item.pop("name").removeprefix("BEOBANK AG ").removeprefix("BEOBANK BR ").removeprefix("BEOBANK PRO CENTER ")
        )
        item["ref"] = response.url.split("/")[-1].replace(".html", "")
        item["country"] = "BE"

        services_text = " ".join(response.xpath("//table[@role='presentation']//p/text()").getall())

        apply_yes_no(Extras.ATM, item, "opname" in services_text.lower() or "retrait" in services_text.lower())
        apply_yes_no(Extras.CASH_IN, item, "storting" in services_text.lower() or "dépôt" in services_text.lower())
        apply_yes_no("parking", item, "parking" in services_text.lower())

        apply_category(Categories.BANK, item)
        yield item
