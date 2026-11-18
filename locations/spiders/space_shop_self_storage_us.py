import re

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature


class SpaceShopSelfStorageUSSpider(Spider):
    name = "space_shop_self_storage_us"
    item_attributes = {"brand": "Space Shop Self Storage", "brand_wikidata": "Q127508446"}
    start_urls = ["https://www.spaceshopselfstorage.com/locations/"]

    def parse(self, response):
        for location in response.xpath('//div[contains(@class, "facility-item")][@data-lat]'):
            item = Feature()
            item["lat"] = location.xpath("@data-lat").get()
            item["lon"] = location.xpath("@data-lng").get()
            item["website"] = item["ref"] = location.xpath('.//a[contains(text(), "View Facility")]/@href').get()
            item["branch"] = (
                location.xpath('.//h4[@class="infowindow-title"]/text()')
                .get()
                .removeprefix("Space Shop Self Storage")
                .strip(" –-")
                .rsplit(" in ", 1)[0]
            )
            address_lines = [
                line.strip() for line in location.xpath('.//p[@class="infowindow-p"]/text()').getall() if line.strip()
            ]
            item["street_address"] = address_lines[0]
            if m := re.match(r"(.+), ([A-Z]{2}) (\d{5})", address_lines[1]):
                item["city"], item["state"], item["postcode"] = m.groups()
            item["phone"] = location.xpath('.//a[starts-with(@href, "tel:")]/span/text()').get()
            apply_category(Categories.SHOP_STORAGE_RENTAL, item)
            yield item
