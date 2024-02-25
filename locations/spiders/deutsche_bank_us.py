import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class DeutscheBankUSSpider(scrapy.Spider):
    name = "deutsche_bank_us"
    item_attributes = {"brand": "Deutsche Bank", "brand_wikidata": "Q66048"}
    start_urls = ["https://country.db.com/usa/contact"]
    no_refs = True

    def parse(self, response):
        for poi in response.xpath(r"//tbody/tr"):
            item = Feature()
            item["street_address"] = poi.xpath("./td[2]/text()").get()
            item["city"] = poi.xpath("./td[3]/text()").get()
            item["postcode"] = poi.xpath("./td[4]/text()").get()
            item["state"] = poi.xpath("./td[1]/text()").get()
            item["website"] = response.url
            apply_category(Categories.BANK, item)

            yield item
