from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature


class EeGBSpider(SitemapSpider):
    name = "ee_gb"
    item_attributes = {"brand": "EE", "brand_wikidata": "Q5322942"}
    sitemap_urls = ["https://ee.co.uk/sitemap-pages.xml"]
    sitemap_rules = [(r"/stores/[^/]+(:?/[^/]+){0,2}/[^/]+", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = response.xpath("//@data-rsid").get()
        item["lat"] = response.xpath("//@data-latitude").get()
        item["lon"] = response.xpath("//@data-longitude").get()
        item["branch"] = response.xpath("//@data-storename").get()
        item["street_address"] = response.xpath('//p[contains(@class, "store__store-address")]/text()').get()
        item["city"] = response.xpath('//p[contains(@class, "store__store-city")]/text()').get()
        item["postcode"] = response.xpath('//p[contains(@class, "store__postcode")]/text()').get()
        item["phone"] = response.xpath('//p[contains(@class, "store__phoneNumber")]/text()').get()
        item["website"] = response.url
        item["street_address"] = response.xpath('//p[contains(@class, "store__store-address")]/text()').get()

        apply_category(Categories.SHOP_MOBILE_PHONE, item)

        yield item
