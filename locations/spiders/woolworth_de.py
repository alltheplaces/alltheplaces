from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class WoolworthDESpider(SitemapSpider, StructuredDataSpider):
    name = "woolworth_de"
    item_attributes = {"brand": "Woolworth", "brand_wikidata": "Q183538"}
    sitemap_urls = ["https://woolworth.de/robots.txt"]
    sitemap_rules = [(".de/stores/store/", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["name"] = None
        item["branch"] = response.xpath("//main/header/h1/text()").get().removeprefix("Woolworth – ")
        item.pop("image")
        item.pop("phone")
        item.pop("email")
        item["website"] = item["extras"]["website:de"] = response.url
        item["extras"]["website:en"] = response.xpath('//link[@rel="alternate"][@hreflang="en-GB"]/@href').get()
        apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
        yield item
