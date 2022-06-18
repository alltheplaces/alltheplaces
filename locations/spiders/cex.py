from locations.items import GeojsonPointItem
from scrapy.spiders import Spider


class CeXSpider(Spider):
    name = "cex"
    item_attributes = {"brand": "CeX", "brand_wikidata": "Q5055676"}
    allowed_domains = ["wss2.cex.uk.webuy.io"]
    start_urls = ["https://wss2.cex.uk.webuy.io/v3/stores"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        for store in response.json()["response"]["data"]["stores"]:
            item = GeojsonPointItem()

            item["ref"] = store["storeId"]
            item["name"] = store["storeName"]
            item["lat"] = store["latitude"]
            item["lon"] = store["longitude"]
            item["phone"] = store["phoneNumber"]
            item["website"] = "https://uk.webuy.com/site/storeDetail/?branchId=" + str(
                store["storeId"]
            )

            yield item
