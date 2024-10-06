from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class PizzaHutFISpider(SitemapSpider):
    name = "pizza_hut_fi"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    sitemap_urls = ["https://pizzahut.fi/sitemap.xml"]
    sitemap_rules = [(r"/toimipisteet/", "parse")]

    def parse(self, response, **kwargs):
        item = Feature()
        item["ref"] = item["website"] = response.url
        address = response.xpath('//*[contains(text(),"Osoite")]/parent::div/p[@class="my-0"]/text()').getall()
        item["addr_full"] = merge_address_lines(address[:2])
        item["email"] = address[-1]
        item["phone"] = response.xpath('//a[contains(@href, "tel")]/text()').get()
        extract_google_position(item, response)
        apply_category(Categories.RESTAURANT, item)
        yield item
