import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class PizzaHutPTSpider(SitemapSpider):
    name = "pizza_hut_pt"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    sitemap_urls = ["https://www.pizzahut.pt/restaurantes-sitemap.xml"]
    sitemap_rules = [(r"/restaurantes/.+", "parse")]

    def parse(self, response, **kwargs):
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["name"] = response.xpath('//meta[@property="og:title"]/@content').get().split(" | Pizza Hut")[0]
        address = merge_address_lines(
            response.xpath('//span[contains(@class, "elementor-heading-title")]/text()').getall()
        )
        if match := re.search(r"(.+?),([\s\d]{9,}).*", address):
            item["addr_full"], item["phone"] = match.groups()
        else:
            item["addr_full"] = address
        apply_category(Categories.RESTAURANT, item)

        yield item
