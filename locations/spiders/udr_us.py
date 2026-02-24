from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.linked_data_parser import LinkedDataParser
from locations.structured_data_spider import StructuredDataSpider


class UdrUSSpider(SitemapSpider, StructuredDataSpider):
    name = "udr_us"
    item_attributes = {
        "operator": "UDR",
        "operator_wikidata": "Q27988153",
    }
    sitemap_urls = ["https://www.udr.com/sitemap.xml"]
    sitemap_rules = [
        (r"^https://www.udr.com/[\w-]+/[\w-]+/[\w-]+/$", "parse"),
    ]
    wanted_types = ["RealEstateListing", "ApartmentComplex"]
    time_format = "%H:%M:%S"

    def iter_linked_data(self, response):
        for ld_obj in super().iter_linked_data(response):
            if (
                "mainEntity" in ld_obj
                and LinkedDataParser.clean_type(ld_obj["mainEntity"].get("@type")) in self.wanted_types
            ):
                yield ld_obj["mainEntity"]
            else:
                yield ld_obj

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["image"] = response.xpath("//meta[@property='og:image']/@content").get()
        apply_category(Categories.RESIDENTIAL_APARTMENTS, item)
        yield item
