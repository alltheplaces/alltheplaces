from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class PizzaHutFISpider(SitemapSpider):
    name = "pizza_hut_fi"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    sitemap_urls = ["https://www.pizzahut.fi/sitemap.xml"]
    sitemap_rules = [("/toimipisteet/", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["street_address"] = response.xpath('//*[@class="yhteystiedot p-4"]/p[2]/text()').get()
        item["addr_full"] = merge_address_lines(
            [item["street_address"], response.xpath('//*[@class="yhteystiedot p-4"]/p[3]/text()').get()]
        )
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]/text()').get()
        item["branch"] = response.xpath("//h2/text()").get()
        item["email"] = response.xpath('//*[contains(text(),"@pizzahut.fi")]/text()').get()
        item["ref"] = item["website"] = response.url
        extract_google_position(item, response)
        apply_category(Categories.RESTAURANT, item)
        yield item
