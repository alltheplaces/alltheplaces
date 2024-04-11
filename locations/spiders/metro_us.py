from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class MetroUSSpider(CrawlSpider, StructuredDataSpider):
    name = "metro_us"
    item_attributes = {"brand": "Metro by T-Mobile", "brand_wikidata": "Q1925685"}
    start_urls = ["https://www.metrobyt-mobile.com/stores/"]
    rules = [
        Rule(LinkExtractor(r"com/stores/\w\w/$")),
        Rule(LinkExtractor(r"com/stores/bd/metro-by-t-mobile-[^/]+-(\d+)/$"), callback="parse_sd"),
    ]
    wanted_types = ["Store"]

    def pre_process_data(self, ld_data, **kwargs):
        ld_data["openingHours"] = ld_data.pop("openingHoursSpecification")

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Metro by T-Mobile ")
        item["street_address"] = (
            item["street_address"].replace(item["postcode"], "").replace(item["state"], "").strip(" ,")
        )
        item.pop("image", None)

        yield item
