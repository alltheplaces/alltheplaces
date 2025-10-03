from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Extras, PaymentMethods, apply_yes_no
from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature


class MilkyLaneZASpider(SitemapSpider):
    name = "milky_lane_za"
    item_attributes = {"brand": "Milky Lane", "brand_wikidata": "Q128223693"}
    sitemap_urls = ["https://locations.milkylane.co.za/site-map.xml"]
    sitemap_rules = [("https://locations.milkylane.co.za/restaurants-", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["branch"] = response.xpath('//*[@id="banner"]//p/text()').get().removeprefix("Milky Lane ")
        item["addr_full"] = response.xpath('//*[@id="location"]//p/text()').get()
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]//text()').get()
        item["email"] = response.xpath('//*[contains(@href,"mailto:")]//text()').get()
        item["ref"] = item["website"] = response.url
        extract_google_position(item, response)
        oh = OpeningHours()
        for day_time in response.xpath('//*[@class="operating-hours flex py-3"]//*[@class="p-3"]'):
            day = day_time.xpath(".//h3/text()").get().strip()
            time = day_time.xpath(".//span/text()").get()
            if time == "Open 24 hours":
                item["opening_hours"] = "24/7"
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
        yield item
