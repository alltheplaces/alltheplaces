from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
import json

from locations.structured_data_spider import StructuredDataSpider
from locations.categories import Categories, apply_category


class SamsicEmploiFRSpider(CrawlSpider, StructuredDataSpider):
    name = "samsic_emploi_fr"
    item_attributes = {"brand": "Samsic Emploi", "brand_wikidata": "Q136431282"}
    allowed_domains = ["www.samsic-emploi.fr"]
    start_urls = ["https://www.samsic-emploi.fr/nos-agences/tous-nos-etablissements"]
    rules = [Rule(LinkExtractor(allow=r"samsic-emploi.fr/nos-agences/[^/]+/[^/]+/[^/]+$"), follow=True, callback="parse_sd" )]

    def iter_linked_data(self, response):
        raw = response.xpath('//script[@type="application/ld+json" and contains(text(), "EmploymentAgency")]/text()').get()
        if raw:
            yield json.loads(raw)["@graph"][0]['itemListElement'][0]

    def post_process_item(self, item, response, ld_data):
        apply_category(Categories.OFFICE_EMPLOYMENT_AGENCY, item)
        item.pop("facebook","")
        item.pop("image","")
        item["branch"] = item.pop("name", "").removeprefix("Samsic Emploi ")
        yield item
