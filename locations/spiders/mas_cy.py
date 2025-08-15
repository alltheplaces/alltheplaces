import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class MasCYSpider(scrapy.Spider):
    name = "mas_cy"
    item_attributes = {"brand": "Mas", "brand_wikidata": "Q122957534"}
    start_urls = [
        "https://www.mas.com.cy/shops/",
    ]

    def parse(self, response, **kwargs):
        for store in response.xpath('//*[@class = "ca-menu"]/li'):
            item = Feature()
            item["name"] = store.xpath("./@data-title").get()
            item["ref"] = store.xpath("./@id").get()
            item["lat"], item["lon"] = store.xpath("./@data-latlon").get().split(",")
            item["phone"] = store.xpath("./@data-phone").get()
            item["addr_full"] = store.xpath("./@data-address").get()
            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item
