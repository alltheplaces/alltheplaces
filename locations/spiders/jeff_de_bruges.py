from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class JeffDeBrugesSpider(SitemapSpider, StructuredDataSpider):
    name = "jeff_de_bruges"
    item_attributes = {
        "brand": "Jeff de Bruges",
        "brand_wikidata": "Q3176626",
        "extras": Categories.SHOP_CHOCOLATE.value,
    }
    sitemap_urls = ["https://www.jeff-de-bruges.com/Assets/Rbs/Seo/100198/en_US/Rbs_Store_Store.1.xml"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["opening_hours"] = OpeningHours()
        for day_time in ld_data["openingHoursSpecification"]:
            day = day_time["dayOfWeek"]
            open_time = day_time["opens"]
            close_time = day_time["closes"]
            item["opening_hours"].add_range(day=day, open_time=open_time, close_time=close_time, time_format="%H:%M:%S")
        yield item
