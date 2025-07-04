from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class SuperStarCarWashUSSpider(SitemapSpider, StructuredDataSpider):
    name = "super_star_car_wash_us"
    item_attributes = {"brand": "Super Star Car Wash", "brand_wikidata": "Q132156104"}
    sitemap_urls = ["https://www.superstarcarwashaz.com/robots.txt"]
    sitemap_rules = [("/location/", "parse")]
    wanted_types = ["AutoWash"]
    time_format = "%I:%M %p"

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name")
        apply_category(Categories.CAR_WASH, item)
        yield item
