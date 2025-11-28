from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class CircleKIrelandSpider(CrawlSpider, StructuredDataSpider):
    name = "circle_k_ireland"
    item_attributes = {"brand": "Circle K", "brand_wikidata": "Q3268010"}
    start_urls = ["https://www.circlek.ie/stations"]
    rules = [Rule(LinkExtractor(allow="/station/circle"), callback="parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        if item["name"].startswith("CIRCLE K EXPRESS "):
            item["branch"] = item.pop("name").removeprefix("CIRCLE K EXPRESS ")
            item["name"] = "Circle K Express"
        elif item["name"].startswith("CIRCLEK EXPRESS "):
            item["branch"] = item.pop("name").removeprefix("CIRCLEK EXPRESS")
        elif item["name"].startswith("CIRCLE K "):
            item["branch"] = item.pop("name").removeprefix("CIRCLE K ")

        item["lat"], item["lon"] = url_to_coords(response.xpath('//a[@class="google-map"]/@href').get())

        apply_category(Categories.FUEL_STATION, item)

        yield item
