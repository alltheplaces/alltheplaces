from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.shahs_halal_food_us import ShahsHalalFoodUSSpider


class ShahsHalalFoodCASpider(Spider):
    name = "shahs_halal_food_ca"
    item_attributes = ShahsHalalFoodUSSpider.item_attributes
    allowed_domains = ["www.shahshalalfood.ca"]
    start_urls = ["https://www.shahshalalfood.ca/restaurants/"]
    no_refs = True

    def parse(self, response: Response) -> Iterable[Feature]:
        for feature in response.xpath('//div[contains(@class, "location-box")]/ul/li'):
            properties = {
                "addr_full": merge_address_lines(
                    feature.xpath('(.//h4[text()="Address"]/following-sibling::p)[1]/text()').getall()
                ),
                "phone": feature.xpath('.//p[contains(text(), "Phone: ")]/text()').get().removeprefix("Phone: "),
                "opening_hours": OpeningHours(),
                "image": feature.xpath('.//div[@class="location-img"]/img/@src').get(),
            }
            hours_text = " ".join(
                feature.xpath('(.//h6[text()="RESTAURANT HOURS"]/following-sibling::p)[1]/text()').getall()
            )
            properties["opening_hours"].add_ranges_from_string(hours_text)
            apply_category(Categories.FAST_FOOD, properties)
            yield Feature(**properties)
