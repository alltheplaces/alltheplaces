import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class GolubCorporationUSSpider(CrawlSpider, StructuredDataSpider):
    name = "golub_corporation_us"
    allowed_domains = ["www.pricechopper.com"]
    start_urls = ["https://www.pricechopper.com/stores/"]
    rules = [
        Rule(LinkExtractor(allow=r"/stores/.*\.html$"), callback="parse_sd"),
        Rule(LinkExtractor(allow=r"/stores/")),
    ]
    brands = {
        "market-32": {"brand": "Market 32", "brand_wikidata": "Q123370878"},
        "market-bistro": {"brand": "Market Bistro", "brand_wikidata": "Q123370887"},
        "price-chopper": {"brand": "Price Chopper", "brand_wikidata": "Q7242574"},
    }
    wanted_types = ["GroceryStore"]

    def post_process_item(self, item, response, ld_data):
        for brand_key, brand_tags in self.brands.items():
            if brand_key in response.url:
                item.update(self.brands[brand_key])
                break
        item["ref"] = re.search(r"\(Store #(\d+)\)", item["name"]).group(1)
        item["name"] = re.sub(r",[A-Z]{2}\s*$", "", re.sub(r"\(Store #\d+\)", "", item["name"]))
        item.pop("facebook", None)
        item.pop("twitter", None)
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
