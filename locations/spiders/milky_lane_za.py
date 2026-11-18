from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, PaymentMethods, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class MilkyLaneZASpider(SitemapSpider, StructuredDataSpider):
    name = "milky_lane_za"
    item_attributes = {"brand": "Milky Lane", "brand_wikidata": "Q128223693"}
    sitemap_urls = ["https://locations.milkylane.co.za/site-map.xml"]
    sitemap_rules = [("https://locations.milkylane.co.za/restaurants-", "parse_sd")]
    wanted_types = ["Restaurant"]
    search_for_email = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Milky Lane ")
        item["image"] = None
        oh = OpeningHours()
        for day_time in response.xpath('//*[@class="operating-hours hidden md:flex"]//*[@class="p-3"]'):
            day = day_time.xpath("./h3/text()").get().strip()
            time = day_time.xpath("./span/text()").get()
            if time == "Open 24 hours":
                oh.add_range(day=day, open_time="00:00", close_time="24:00")
            elif time == "Closed":
                oh.set_closed(day)
            else:
                open_time, close_time = time.split(" | ")
                oh.add_range(day=day, open_time=open_time, close_time=close_time, time_format="%I:%M %p")
        item["opening_hours"] = oh
        attributes = response.xpath('//*[@class = "p-2"]//text()').getall()
        apply_yes_no(Extras.DELIVERY, item, "Delivery" in attributes)
        apply_yes_no(PaymentMethods.CARDS, item, "Card" in attributes)
        apply_yes_no(PaymentMethods.DEBIT_CARDS, item, "Debit cards" in attributes)
        apply_yes_no(PaymentMethods.CREDIT_CARDS, item, "Credit cards" in attributes)
        apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive-through" in attributes)
        apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive Thru" in attributes)
        apply_yes_no(Extras.BREAKFAST, item, "Breakfast" in attributes)
        apply_yes_no(Extras.BRUNCH, item, "Brunch" in attributes)
        apply_category(Categories.ICE_CREAM, item)
        yield item
