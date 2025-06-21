from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class MarketLiquorsNAZASpider(Spider):
    name = "market_liquors_na_za"
    item_attributes = {"brand": "Market Liquors", "brand_wikidata": "Q116895063"}
    allowed_domains = ["marketliquors.co.za"]
    start_urls = ["https://marketliquors.co.za/store-locator/"]
    no_refs = True

    def parse(self, response: Response) -> Iterable[Feature]:
        for store in response.xpath('.//div[contains(@class, "mk-text-block")]'):
            properties = {
                "branch": store.xpath('./h3/strong/text()').get().removeprefix("Market Liquors "),
                "country": store.xpath('(./ancestor::div[contains(@class, "wpb_row")]/preceding-sibling::div/div/div/h2[contains(@class, "mk-fancy-title")]/span/p/span/text())[last()]').get().removeprefix("MARKET LIQUORS "),
                "opening_hours": OpeningHours(),
            }
            if addr_full := merge_address_lines(store.xpath('./p/text()').getall()):
                properties["addr_full"] = addr_full.split("Telephone:", 1)[0]
            elif addr_full := merge_address_lines(store.xpath('./div/p/text()').getall()):
                properties["addr_full"] = addr_full.split("Telephone:", 1)[0]
            if phone_line := store.xpath('./p/strong[contains(text(), "Telephone: ")]/text()').get():
                properties["phone"] = phone_line.removeprefix("Telephone: ")
            hours_string = " ".join(store.xpath('.//span[@class="trading-hours-day"]/text()').getall())
            properties["opening_hours"].add_ranges_from_string(hours_string)
            apply_category(Categories.SHOP_ALCOHOL, properties)
            yield Feature(**properties)
