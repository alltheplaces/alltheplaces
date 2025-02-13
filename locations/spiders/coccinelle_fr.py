import json
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines

BRANDS = {
    "coccimarket": {"brand": "CocciMarket", "brand_wikidata": "Q90020480"},
    "coccimarket city": {"brand": "CocciMarket City", "brand_wikidata": "Q90020481"},
    "coccimarket easy": {"brand": "CocciMarket Easy", "name": "CocciMarket Easy"},
    "coccinelle express": {"brand": "Coccinelle Express", "brand_wikidata": "Q90020479"},
    "coccinelle supermarche": {"brand": "Coccinelle Supermarché", "brand_wikidata": "Q90020459"},
}


class CoccinelleFRSpider(SitemapSpider):
    name = "coccinelle_fr"
    sitemap_urls = ["https://www.coccinelle.fr/sitemap.xml"]
    sitemap_rules = [("/magasin/", "parse")]

    def sitemap_filter(self, entries):
        for entry in entries:
            entry["loc"] = entry["loc"].replace("http://default/", "https://www.coccinelle.fr/")
            yield entry

    def parse(self, response: Response, **kwargs: Any) -> Any:
        location = json.loads(response.xpath('//script[contains(text(),"rndmaps")]/text()').get())["rndmaps"]
        item = Feature()
        item["lat"] = location.get("lat")
        item["lon"] = location.get("lng")
        item["ref"] = response.xpath("//@data-shop").get()
        item["branch"] = response.xpath('//meta[@property="og:title"]/@content').get("").split("|")[0].strip().title()
        item["website"] = response.url
        item["street_address"] = merge_address_lines(
            [
                response.xpath('//*[contains(@class,"addr-1")]/text()').get(""),
                response.xpath('//*[contains(@class,"addr-2")]/text()').get(""),
            ]
        )
        item["city"] = response.xpath('//*[contains(@class,"city")]/text()').get("").title()
        item["postcode"] = response.xpath('//*[contains(@class,"zipcode")]/text()').get()
        item["phone"] = response.xpath('//a[contains(@href,"tel:")]/@href').get()
        brand_key = (
            response.xpath('//img[@alt="logo coccinelle"]/following-sibling::*[contains(@class,"poppins")]/text()')
            .get("")
            .strip()
            .lower()
        )
        if brand_info := BRANDS.get(brand_key):
            item.update(brand_info)
        else:
            self.logger.error("Unexpected type: {}".format(brand_key))
        if brand_key == "coccimarket easy":
            apply_category(Categories.SHOP_CONVENIENCE, item)
        yield item
