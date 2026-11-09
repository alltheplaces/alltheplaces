from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours, sanitise_day
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class EcomiamFRSpider(CrawlSpider, StructuredDataSpider):
    name = "ecomiam_fr"
    item_attributes = {"brand": "Écomiam", "brand_wikidata": "Q130215661", "name": "Écomiam"}
    allowed_domains = ["www.ecomiam.com"]
    start_urls = ["https://www.ecomiam.com/magasins.php"]
    rules = [Rule(LinkExtractor(allow=r"/magasins-ecomiam-[^/]+-mgn-\d+\.html$"), callback="parse_sd")]
    wanted_types = ["Store"]
    search_for_twitter = False
    search_for_facebook = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["ref"] = response.url.removesuffix(".html").rsplit("-", 1)[1]
        item["branch"] = item.pop("name").removeprefix("écomiam ")
        item.pop("image", None)

        oh = OpeningHours()
        for row in response.css(".grid-magasin-schedules tr"):
            day = sanitise_day(row.css("td::text").get("").strip(), DAYS_FR)
            if not day:
                continue
            slots = row.css(".magasin_slot::text").getall()
            if not slots:
                oh.set_closed(day)
            for slot in slots:
                oh.add_range(day, *slot.split(" - "))
        item["opening_hours"] = oh

        apply_category(Categories.SHOP_FROZEN_FOOD, item)
        yield item
