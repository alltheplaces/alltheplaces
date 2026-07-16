from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BeobankBESpider(CrawlSpider, StructuredDataSpider):
    name = "beobank_be"
    item_attributes = {"brand": "Beobank", "brand_wikidata": "Q14911971"}
    start_urls = ["https://www.beobank.be/fr/agences/regions.html"]
    rules = [
        Rule(LinkExtractor(restrict_xpaths='//*[@class="ei_richlinkmenuitem"]')),
        Rule(
            LinkExtractor(
                allow=r"https://www.beobank.be/fr/agences/ResultatsRechercheGeographique.aspx?inseeCode=\d+&postalCode=\d+"
            )
        ),
        Rule(
            LinkExtractor(allow=r"https://www.beobank.be/fr/agence/region-[^/]+/[^/]+/\d+\.html$"), callback="parse_sd"
        ),
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        if ld_data.get("geo"):
            return
        item["branch"] = (
            item.pop("name")
            .removeprefix("BEOBANK AG ")
            .removeprefix("BEOBANK BR ")
            .removeprefix("BEOBANK PRO CENTER ")
        )
        item["ref"] = response.url
        item["country"] = "BE"

        services_text = " ".join(response.xpath("//table[@role='presentation']//p/text()").getall())

        apply_yes_no(Extras.ATM, item, "opname" in services_text.lower() or "retrait" in services_text.lower())
        apply_yes_no(Extras.CASH_IN, item, "storting" in services_text.lower() or "dépôt" in services_text.lower())
        apply_yes_no("parking", item, "parking" in services_text.lower())

        apply_category(Categories.BANK, item)
        yield item
