import json

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_yes_no
from locations.structured_data_spider import StructuredDataSpider


class CreditAgricoleSpider(SitemapSpider, StructuredDataSpider):
    name = "credit_agricole"
    item_attributes = {"brand": "Crédit Agricole", "brand_wikidata": "Q590952", "extras": Categories.BANK.value}
    allowed_domains = ["credit-agricole.fr"]
    sitemap_urls = ["https://www.credit-agricole.fr/robots.txt"]
    sitemap_rules = [(r"/particulier/agence/[-\w]+/([-\w]+)\.html$", "parse_sd")]
    wanted_types = ["FinancialService"]
    time_format = "%H:%M:%S"

    def post_process_item(self, item, response, ld_data, **kwargs):
        if name := ld_data.get("Name"):
            ld_data["name"] = name

        if geodata := response.xpath('//div[@class="npc-sl-strct-map Card js-CardAgencyMap"]/@data-value').get():
            coords = json.loads(geodata)
            item["lat"] = coords["latitude"]
            item["lon"] = coords["longitude"]

        if (
            "guichets automatiques"
            in response.xpath('//span[@class="npc-sl-strct-srv-card--text "]/text()').get(default="").lower()
        ):
            apply_yes_no(Extras.ATM, item, True)

        yield item
