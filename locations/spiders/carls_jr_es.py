from scrapy.spiders import SitemapSpider

from locations.spiders.carls_jr_us import CarlsJrUSSpider
from locations.structured_data_spider import StructuredDataSpider


class CarlsJrESSpider(SitemapSpider, StructuredDataSpider):
    name = "carls_jr_es"
    item_attributes = CarlsJrUSSpider.item_attributes
    sitemap_urls = ["https://carlsjr.es/ubicaciones-sitemap.xml"]
    sitemap_rules = [(r"/ubicaciones/", "parse_sd")]
    wanted_types = ["WebPage"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = item["name"].removesuffix(" - Carls Jr.")
        item["addr_full"] = response.xpath('//*[@itemprop="text"]/p/text()').get()
        item["email"] = None
        item["extras"]["check_date"] = (ld_data.get("dateModified") or ld_data.get("datePublished")).split("T", 1)[0]
        yield item
