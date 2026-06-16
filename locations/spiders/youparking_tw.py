from typing import Iterable

from scrapy.http import TextResponse

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class YouParkingTWSpider(JSONBlobSpider):
    name = "youparking_tw"
    item_attributes = {"brand": "俥亭停車", "brand_wikidata": "Q132009628"}
    start_urls = ["https://www.youparking.com.tw/parking-list.php"]

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        for location in response.xpath("//tbody/tr"):
            item = Feature()
            item["name"] = location.xpath("./td[4]/text()").get()
            item["state"] = location.xpath("./td[1]/text()").get()
            item["city"] = location.xpath("./td[2]/text()").get()
            item["addr_full"] = location.xpath("./td[3]/text()").get()
            item["ref"] = item["website"] = response.urljoin(
                location.xpath("./@onclick").get().removeprefix("location.href=").replace("'", "")
            )
            yield item
