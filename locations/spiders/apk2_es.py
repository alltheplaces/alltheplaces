from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class Apk2ESSpider(CrawlSpider, StructuredDataSpider):
    name = "apk2_es"
    start_urls = ["https://apk2gestion.com/es/buscar"]
    item_attributes = {"brand": "APK2", "brand_wikidata": "Q124151387"}
    rules = [
        Rule(
            LinkExtractor(restrict_xpaths='//div[@class="c-search-list__wrapper"]/a', allow="/es/parking/"),
            callback="parse_sd",
        )
    ]
    wanted_types = ["parkingfacility"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.PARKING, item)
        item["ref"] = response.url
        item["branch"] = item.pop("name")
        item.pop("phone")
        item.pop("email")
        yield item
