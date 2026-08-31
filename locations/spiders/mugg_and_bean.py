from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, PaymentMethods, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class MuggAndBeanSpider(SitemapSpider, StructuredDataSpider):
    name = "mugg_and_bean"
    item_attributes = {"brand": "Mugg & Bean", "brand_wikidata": "Q6932113"}
    sitemap_urls = [
        "https://locations.muggandbean.co.za/site-map.xml",
        "https://malawilocations.muggandbean.africa/site-map.xml",
        "https://mauritiuslocations.muggandbean.africa/site-map.xml",
    ]
    sitemap_rules = [("/restaurants-", "parse")]
    wanted_types = ["Restaurant"]
    search_for_email = False

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if item["name"].startswith("Mugg & Bean On The Move "):
            item["branch"] = item.pop("name").removeprefix("Mugg & Bean On The Move ")
            item["name"] = "Mugg & Bean On The Move"
        elif item["name"].startswith("Mugg & Bean "):
            item["branch"] = item.pop("name").removeprefix("Mugg & Bean ")
            item["name"] = "Mugg & Bean"
        item["image"] = None
        item["addr_full"] = response.xpath('//*[@id="location"]//p/text()').get()
        oh = OpeningHours()
        for day_time in response.xpath('//*[@class="operating-hours flex py-3"]//*[@class="p-3"]'):
            day = day_time.xpath(".//h3/text()").get().strip()
            time = day_time.xpath(".//span/text()").get()
            if time == "Open 24 hours":
                item["opening_hours"] = "24/7"
            elif time == "Closed":
                oh.set_closed(day)
            else:
                open_time, close_time = day_time.xpath(".//span/text()").get().split(" | ")
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

        apply_category(Categories.CAFE, item)

        yield item
