from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.items import Feature
from locations.spiders.mcdonalds import McdonaldsSpider


class McdonaldsVNSpider(Spider):
    name = "mcdonalds_vn"
    item_attributes = McdonaldsSpider.item_attributes
    start_urls = ["https://mcdonalds.vn/restaurants.html"]

    def parse(self, response):
        for location in response.xpath('//div[@class="tbox-address-store"]'):
            item = Feature()
            item["ref"] = location.xpath("@id").get()
            item["name"] = location.xpath('./p[@class="tname-store"]/text()').get()
            item["addr_full"] = location.xpath('./p[@class="ttitle"][contains(., "Address:")]/span/text()').get()
            item["phone"] = location.xpath('/p[@class="ttitle"][contains(., "Phone:")]/span/text()').get()
            item["lat"], item["lon"] = url_to_coords(location.xpath('.//a[@class="location-web"]/@href').get())

            apply_category(Categories.FAST_FOOD, item)

            yield item
