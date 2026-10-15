import json

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature, set_closed
from locations.structured_data_spider import StructuredDataSpider


class GiantFoodUSSpider(SitemapSpider, StructuredDataSpider):
    name = "giant_food_us"
    item_attributes = {"brand": "Giant", "brand_wikidata": "Q5558336"}
    allowed_domains = ["giantfood.com"]
    sitemap_urls = ["https://stores.giantfood.com/robots.txt"]
    sitemap_rules = [(r"com/\w\w/[^/]+/\d+-[^/]+$", "parse")]
    wanted_types = ["GroceryStore"]
    drop_attributes = {"facebook", "twitter"}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        if "CLOSED" in response.xpath("//title/text()").get(""):
            set_closed(item)

        item["ref"] = response.xpath('//div[@class="StoreDetails-storeNum"]/text()').get()
        item["branch"] = item.pop("name").removeprefix("Giant Food ")

        try:
            item["opening_hours"] = self.parse_opening_hours(response)
        except Exception:
            pass

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item

    @staticmethod
    def parse_opening_hours(response: Response) -> OpeningHours:
        # The microdata openingHours belong to the pharmacy, so read the store hours widget instead
        days = response.xpath(
            '//*[@data-ya-scope="info"]//*[contains(@class, "c-location-hours-details-wrapper")]/@data-days'
        ).get()
        oh = OpeningHours()
        for day in json.loads(days):
            for interval in day["intervals"]:
                oh.add_range(
                    day["day"],
                    f"{interval['start']:04d}",
                    f"{interval['end']:04d}",
                    time_format="%H%M",
                )
        return oh
