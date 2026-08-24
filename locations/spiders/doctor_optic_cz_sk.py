from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser
from locations.structured_data_spider import StructuredDataSpider

# Store pages use a non-standard schema.org "@type" ("Oční optika", i.e.
# "Eye optics" in Czech), so the default StructuredDataSpider wanted_types
# filtering is bypassed via the iter_linked_data() override below.
COUNTRY_NAME_TO_CODE = {
    "Czech Republic": "CZ",
    "Slovakia": "SK",
}


class DoctorOpticCZSKSpider(SitemapSpider, StructuredDataSpider):
    name = "doctor_optic_cz_sk"
    item_attributes = {"brand": "Doctor Optic", "brand_wikidata": "Q140307589"}
    sitemap_urls = ["https://doctoroptic.cz/stores-sitemap.xml"]
    sitemap_rules = [(r"/ocni-optika/[^/]+/$", "parse_sd")]

    def iter_linked_data(self, response: Response) -> Iterable[dict]:
        for ld_obj in LinkedDataParser.iter_linked_data(response):
            if ld_obj.get("@type") == "Oční optika":
                yield ld_obj

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Any:
        if country := item.get("country"):
            item["country"] = COUNTRY_NAME_TO_CODE.get(country, country)

        # Some store pages give a generic brand/franchise page (e.g.
        # "https://www.droptic.sk/prevadzky/") as the linked data "url"
        # rather than the specific store page, so always prefer the URL of
        # the page actually crawled.
        item["website"] = response.url

        apply_category(Categories.SHOP_OPTICIAN, item)

        yield item
