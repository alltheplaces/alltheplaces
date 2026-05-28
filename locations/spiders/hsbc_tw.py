from requests_cache import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class HsbcTWSpider(StructuredDataSpider):
    name = "hsbc_tw"
    item_attributes = {"brand": "HSBC", "brand_wikidata": "Q5635861"}
    start_urls = ["https://www.hsbc.com.tw/en-tw/ways-to-bank/branch/"]

    def parse(self, response: Response):
        for location in response.xpath('//*[@class="desktop"]//tbody//tr'):
            item = Feature()
            item["city"] = location.xpath("./td[1]//text()").get()
            item["branch"] = location.xpath("./td[2]//text()").get().removesuffix(" Branch")
            item["addr_full"] = location.xpath("./td[3]//text()").get()
            item["phone"] = location.xpath("./td[4]//text()").get()
            item["ref"] = location.xpath("./td[5]//text()").get()

            apply_category(Categories.BANK, item)

            yield item
