from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

FUEL_TYPES_MAPPING = {
    "CNG": Fuel.CNG,
    "Diesel": Fuel.DIESEL,
    "Dyed Diesel": Fuel.UNTAXED_DIESEL,
    "E85": Fuel.E85,
    "E15": Fuel.E15,
    "Kerosene": Fuel.KEROSENE,
    "Midgrade - Ethanol Free": Fuel.ETHANOL_FREE,
    "Midgrade": Fuel.OCTANE_87,
    "Premium - Ethanol Free": Fuel.ETHANOL_FREE,
    "Premium Plus (93 octane)": Fuel.OCTANE_93,
    "Premium": Fuel.OCTANE_91,
    "Super Unleaded/Regular": Fuel.OCTANE_87,
    "Xtreme Diesel": Fuel.DIESEL,
}


class KumAndGoSpider(CrawlSpider, StructuredDataSpider):
    name = "kum_and_go"
    item_attributes = {"brand": "Kum & Go", "brand_wikidata": "Q6443340"}
    start_urls = ["https://locations.kumandgo.com/index.html"]
    rules = [
        Rule(LinkExtractor(r"https://locations.kumandgo.com/[a-z]{2}$")),
        Rule(LinkExtractor(r"https://locations.kumandgo.com/[a-z]{2}/[-\w]+$")),
        Rule(LinkExtractor(r"https://locations.kumandgo.com/[a-z]{2}/[-\w]+/[-\w]+"), callback="parse_sd"),
    ]
    skip_auto_cc_spider_name = True

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        fuels = set(response.xpath('//*[@class="FuelPrices-fuelTitle"]/text()').getall())
        if fuels:
            apply_category(Categories.FUEL_STATION, item)
            for fuel in fuels:
                if tag := FUEL_TYPES_MAPPING.get(fuel):
                    apply_yes_no(tag, item, True)
                else:
                    self.crawler.stats.inc_value(f"kum_and_go/fuel_not_mapped/{fuel}")
        else:
            apply_category(Categories.SHOP_CONVENIENCE, item)

        yield item
