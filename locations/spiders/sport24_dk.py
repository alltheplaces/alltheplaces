from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature


class Sport24DKSpider(SitemapSpider):
    name = "sport24_dk"
    item_attributes = {"brand": "Sport 24", "brand_wikidata": "Q121503172"}
    sitemap_urls = ["https://www.sport24.dk/sitemap-0.xml"]
    sitemap_rules = [(r"/stores/sport24.*", "parse")]

    def parse(self, response, **kwargs):
        item = Feature()
        item["name"] = response.xpath("//title/text()").get()
        item["website"] = item["ref"] = response.url
        item["street_address"] = response.xpath('//*[@class = " mx-auto"]//p[2]/text()').get()
        item["postcode"] = response.xpath('//*[@class = "mb-2"]/text()').get()
        item["city"] = response.xpath('//*[@class = "mb-2"]/text()[3]').get()
        item["email"] = response.xpath('//*[contains(@href,"mailto")]//text()').get()
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]//text()').get()
        extract_google_position(item, response)
        if "island" in item["name"].lower():
            item["country"] = "IS"
        elif "Grønland" in item["name"]:
            item["country"] = "GL"
        else:
            item["country"] = "DK"

        apply_category(Categories.SHOP_SPORTS, item)

        yield item
