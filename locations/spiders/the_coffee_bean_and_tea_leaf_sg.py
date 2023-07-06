from locations.hours import OpeningHours
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class TheCoffeeBeanAndTeaLeafSGSpider(AmastyStoreLocatorSpider):
    name = "the_coffee_bean_and_tea_leaf_sg"
    item_attributes = {"brand": "The Coffee Bean & Tea Leaf", "brand_wikidata": "Q1141384"}
    allowed_domains = ["www.coffeebean.com.sg"]

    def parse_item(self, item, location, popup_html):
        item["name"] = popup_html.xpath('//a[contains(@class, "amlocator-link")]/text()').get().strip()
        item["addr_full"] = " ".join(
            (
                " ".join(
                    popup_html.xpath(
                        '//div[contains(@class, "amlocator-info-popup")]/div[contains(@class, "amlocator-image")]/following-sibling::text()'
                    ).getall()
                )
            ).split()
        )
        item["website"] = popup_html.xpath('//a[contains(@class, "amlocator-link")]/@href').get()

        oh = OpeningHours()
        hours_raw = (
            " ".join(
                (
                    " ".join(popup_html.xpath('//div[contains(@class, "amlocator-description")]//text()').getall())
                ).split()
            )
            .replace("24 Hours", "12:00am to 11:59pm")
            .replace("Operating Daily,", "Mon-Sun")
        )
        oh.add_ranges_from_string(hours_raw)
        item["opening_hours"] = oh.as_opening_hours()

        yield item
