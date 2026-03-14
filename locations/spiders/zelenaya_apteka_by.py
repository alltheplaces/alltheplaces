import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class ZelenayaAptekaBYSpider(scrapy.Spider):
    name = "zelenaya_apteka_by"
    item_attributes = {
        "brand": "Зелёная Аптека",
        "brand_wikidata": "Q123362420",
        "extras": {"brand:en": "Zelenaya Apteka"},
    }
    start_urls = ["https://fito.by/shops/"]
    no_refs = True

    def parse(self, response, **kwargs):
        for store in response.xpath('//*[@id="stores-list"]/*[@data-coords]'):
            item = Feature()
            item["branch"] = store.xpath('.//*[@class="title"]/text()').get()
            item["street_address"] = store.xpath('.//*[@class="address"]/text()').get()
            item["lat"], item["lon"] = store.xpath("./@data-coords").get().strip("[]").split(",")
            item["phone"] = store.xpath('.//a[contains(@href, "tel:")]/@href').get()
            apply_category(Categories.PHARMACY, item)
            yield item
