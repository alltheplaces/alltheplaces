from scrapy.spiders import SitemapSpider

from locations.categories import apply_category
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
    wanted_types = ["ApartmentComplex"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["image"] = response.xpath("//meta[@property='og:image']/@content").get()
        apply_category({"landuse": "residential", "residential": "apartments"}, item)
        yield item
