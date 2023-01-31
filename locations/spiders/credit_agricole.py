import json

from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class CreditAgricoleSpider(SitemapSpider, StructuredDataSpider):
    name = "credit_agricole"
    item_attributes = {"brand": "Credit Agricole", "brand_wikidata": "Q590952", "extras": Categories.BANK.value}
    allowed_domains = ["credit-agricole.fr"]
    sitemap_urls = ["https://www.credit-agricole.fr/robots.txt"]
    sitemap_rules = [(r"/particulier/agence/[-\w]+/([-\w]+)\.html$", "parse_sd")]
    wanted_types = ["FinancialService"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if name := ld_data.get("Name"):
            ld_data["name"] = name

        if geodata := response.xpath('//div[@class="CardAgencyMap js-CardAgencyMap"]/@data-value').get():
            coords = json.loads(geodata)
            item["lat"] = coords["latitude"]
            item["lon"] = coords["longitude"]

        item["opening_hours"] = OpeningHours()
        item["opening_hours"].from_linked_data(ld_data, "%H:%M:%S")

        yield item
