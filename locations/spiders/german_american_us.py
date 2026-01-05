from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature


class GermanAmericanUSSpider(SitemapSpider):
    name = "german_american_us"
    item_attributes = {"brand": "German American", "brand_wikidata": "Q120753420"}
    sitemap_urls = ["https://germanamerican.com/sitemap.xml"]
    sitemap_rules = [(r"locations\/(?!.*(all-locations)).*", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["branch"] = response.xpath('//*[@class= "location-info"]//h1/text()').get()
        item["street_address"] = response.xpath('//*[@class= "location-info"]//p//text()').get()
        item["addr_full"] = ",".join(
            [item["street_address"], response.xpath('//*[@class="location-address"]').xpath("normalize-space()").get()]
        )
        item["ref"] = item["website"] = response.url
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]/text()').get()
        if "atm" in response.url:
            apply_category(Categories.ATM, item)
        else:
            apply_category(Categories.BANK, item)
        yield item
