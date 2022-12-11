from scrapy import Spider

from locations.items import GeojsonPointItem


class HeartOfEnglandCooperativeSpider(Spider):
    name = "heart_of_england_cooperative"
    item_attributes = {
        "brand": "Heart of England Co-operative",
        "brand_wikidata": "Q5692254",
        "country": "GB",
    }
    start_urls = ["https://www.cawtest.com/heartofengland/wp-content/plugins/superstorefinder-wp/ssf-wp-xml.php"]

    def parse(self, response):
        for store in response.xpath("/locator/store/item"):
            item = GeojsonPointItem()

            item["name"] = store.xpath("./location/text()").get()
            item["addr_full"] = store.xpath("./address/text()").get()
            item["ref"] = store.xpath("./sortord/text()").get()
            item["lat"] = store.xpath("./latitude/text()").get()
            item["lon"] = store.xpath("./longitude/text()").get()
            item["website"] = store.xpath("./website/text()").get()
            item["phone"] = store.xpath("./telephone/text()").get()

            yield item
