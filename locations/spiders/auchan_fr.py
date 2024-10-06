from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class AuchanFRSpider(CrawlSpider, StructuredDataSpider):
    name = "auchan_fr"
    item_attributes = {"brand": "Auchan", "brand_wikidata": "Q758603"}
    start_urls = [
        "https://www.auchan.fr/nos-magasins",
        "https://www.auchan.fr/nos-magasins?types=DRIVE",
        "https://www.auchan.fr/nos-magasins?types=SUPER",
    ]
    rules = [
        Rule(LinkExtractor(allow=["/hypermarche/"]), callback="parse_sd"),
        Rule(LinkExtractor(allow=["/drive/"]), callback="parse_sd"),
        Rule(LinkExtractor(allow=["/supermarche/"]), callback="parse_sd"),
    ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = item["name"].replace("Supermarché Supermarché", "Supermarché")
        item["lat"] = response.xpath("//@data-lat").get()
        item["lon"] = response.xpath("//@data-lng").get()
        if "supermarche" in response.url:
            item["brand"] = "Auchan Supermarché"
            item["brand_wikidata"] = "Q105857776"
        if "drive" in response.url:
            item["brand"] = "Auchan Drive"
            item["brand_wikidata"] = "Q2870659"
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
