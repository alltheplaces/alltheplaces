from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature


class VibraHotelsESSpider(SitemapSpider):
    name = "vibra_hotels_es"
    item_attributes = {"brand": "Vibra Hotels", "brand_wikidata": "Q126183090"}
    sitemap_urls = ["https://www.vibrahotels.com/sitemap.xml"]
    sitemap_rules = [(r"/es/.+/ubicacion$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        location = response.xpath('//*[contains(@class, "subtitle-location-section")]/parent::div')
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["branch"] = location.xpath(".//p[1]/text()").get()
        item["addr_full"] = location.xpath(".//p[2]/text()").get()
        item["phone"] = location.xpath('.//*[contains(text(),"T:")]/text()').get()
        item["email"] = location.xpath('.//*[contains(text(),"E:")]/text()').get("").replace("E: ", "")
        if "apartamentos" in response.url:
            apply_category(Categories.TOURISM_APARTMENT, item)
        else:
            apply_category(Categories.HOTEL, item)
        yield item
