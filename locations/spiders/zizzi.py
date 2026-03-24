from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class ZizziSpider(CrawlSpider, StructuredDataSpider):
    name = "zizzi"
    item_attributes = {"brand": "Zizzi", "brand_wikidata": "Q122921301"}
    start_urls = [
        "https://www.zizzi.no/finn-butikk/",
        "https://www.zizzi.dk/find-butik/",
        "https://www.zizzi.fi/loyda-myymala/",
        "https://www.zizzi.nl/vind-een-winkel/",
        "https://www.zizzi.se/hitta-butik/",
    ]
    rules = [
        Rule(
            LinkExtractor(allow=r"/find-butik|finn-butikk|loyda-myymala|vind-een-winkel|hitta-butik/"),
            callback="parse_sd",
        )
    ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = response.url
        item["branch"] = item.pop("name").replace("Zizzi ", "")
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
