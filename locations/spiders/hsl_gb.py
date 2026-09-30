
from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature


class HslGBSpider(Spider):
    name = "hsl_gb"
    item_attributes = {"brand": "HSL", "brand_wikidata": "Q64284324"}
    start_urls = ["https://www.hslchairs.com/find-a-showroom"]

    def parse(self, response):
        for location in response.xpath(
            '//div[@class="card-item card-showroom border-0 bg-lightgrey text-base overflow-hidden h-full"]'
        ):
            print(location)
            item = Feature()
            item["branch"] = location.xpath('//h4[@class="mb-0"]/text()').get()
            item["addr_full"] = location.xpath('//p[@class="mb-3"]/text()').get()
            item["phone"] = location.xpath('//p[contains(text(), "0")]/text()').get()
            item["ref"] = item["website"] = location.xpath(
                '//a[contains(@href,"https://www.hslchairs.com/find-a-showroom/")]/@href'
            ).get()
            item["lat"], item["lon"] = (
                location.xpath('.//a[contains(@href, "https://www.google.com/maps/dir/?api=1&destination=")]/@href')
                .get()
                .replace("https://www.google.com/maps/dir/?api=1&destination=", "")
                .split(",")
            )

            apply_category(Categories.SHOP_FURNITURE, item)
            yield item
