from scrapy import Spider

from locations.categories import Categories
from locations.google_url import extract_google_position
from locations.items import Feature


class FlashCoffeeIDSpider(Spider):
    name = "flash_coffee_id"
    item_attributes = {
        "brand": "Flash Coffee",
        "brand_wikidata": "Q118627777",
        "extras": Categories.CAFE.value,
    }
    start_urls = ["https://flash-coffee.com/locations/"]

    def parse(self, response):
        for location in response.xpath(
            '//*[@class = "wp-block-group alignfull is-layout-flow wp-block-group-is-layout-flow"]'
        ):
            item = Feature()
            item["branch"] = item["ref"] = location.xpath(".//p/strong/text()").get()
            item["addr_full"] = location.xpath(".//p/text()").get()
            extract_google_position(item, location)
            yield item
