import json

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.structured_data_spider import StructuredDataSpider


class CreditAgricoleSpider(SitemapSpider, StructuredDataSpider):
    name = "credit_agricole"
    item_attributes = {"brand": "Crédit Agricole", "brand_wikidata": "Q590952"}
    allowed_domains = ["credit-agricole.fr"]
    sitemap_urls = ["https://www.credit-agricole.fr/robots.txt"]
    sitemap_rules = [(r"/particulier/agence/[-\w]+/([-\w]+)\.html$", "parse_sd")]
    wanted_types = ["FinancialService"]
    time_format = "%H:%M:%S"

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Agence Crédit Agricole ")

        if geodata := response.xpath('//div[@class="npc-sl-strct-map Card js-CardAgencyMap"]/@data-value').get():
            coords = json.loads(geodata)
            item["lat"] = coords["latitude"]
            item["lon"] = coords["longitude"]

        services = response.xpath('//span[@class="npc-sl-strct-srv-card--text "]/text()').getall()
        apply_yes_no(Extras.ATM, item, any("distributeur" in s.lower() and "billets" in s.lower() for s in services))
        apply_category(Categories.BANK, item)

        yield item
