from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

CHARTER = {"brand": "Charter", "brand_wikidata": "Q95916752"}


class ConsumESSpider(SitemapSpider, StructuredDataSpider):
    name = "consum_es"
    item_attributes = {"brand": "Consum", "brand_wikidata": "Q8350308"}
    sitemap_urls = ["https://www.consum.es/robots.txt"]
    sitemap_rules = [(r"es/supermercados/([^/]+)/", "parse")]
    wanted_types = ["Store"]
    requires_proxy = True

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name")
        item["website"] = response.url

        if ld_data.get("description") == "Charter":
            item.update(CHARTER)

        item["extras"]["website:es"] = response.xpath('//link[@rel="alternate"][@hreflang="es"]/@href').get()
        item["extras"]["website:ca"] = response.xpath('//link[@rel="alternate"][@hreflang="ca"]/@href').get()
        item["extras"]["website:en"] = response.xpath('//link[@rel="alternate"][@hreflang="en"]/@href').get()

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
