from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class CerballianceSpider(SitemapSpider, StructuredDataSpider):
    name = "cerballiance"
    item_attributes = {"brand": "Cerballiance", "brand_wikidata": "Q106686993"}
    sitemap_urls = ["https://laboratoires.cerballiance.fr/robots.txt"]
    sitemap_rules = [(r"fr/[^/]+/[^/]+/[^/]+$", "parse")]
    wanted_types = ["MedicalClinic"]
    search_for_twitter = False
    search_for_facebook = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["image"] = None
        item["branch"] = (
            item.pop("name")
            .removeprefix("Laboratoire de Biologie Médicale - ")
            .removeprefix("Laboratoire d'analyses médicales - ")
            .removeprefix("Laboratoire de Biologie de la Reproduction - ")
            .removeprefix("Laboratoire d'analyses médicales 24/7 - ")
            .removeprefix("Laboratoire d’analyses médicales - ")
            .removeprefix("Laboratoire de biologie médicale - ")
            .removesuffix(" - Cerballiance")
        )

        apply_category(Categories.MEDICAL_LABORATORY, item)
        yield item
