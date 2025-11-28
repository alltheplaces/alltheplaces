from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class CataloniaHotelsSpider(CrawlSpider, StructuredDataSpider):
    name = "catalonia_hotels"
    item_attributes = {"brand": "Catalonia Hotels & Resorts", "brand_wikidata": "Q126180437"}
    start_urls = ["https://www.cataloniahotels.com/en"]
    rules = [Rule(LinkExtractor(allow=r"/en/hotel/catalonia-[-\w]+$"), callback="parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if "Resort" in item["name"]:
            apply_category(Categories.LEISURE_RESORT, item)
        else:
            apply_category(Categories.HOTEL, item)
        item["branch"] = (
            item.pop("name")
            .removeprefix("Catalonia ")
            .removesuffix(
                "Resort",
            )
        )
        yield item
