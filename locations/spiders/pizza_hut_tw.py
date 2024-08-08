from scrapy import Spider

from locations.items import Feature


class PizzaHutTWSpider(Spider):
    name = "pizza_hut_tw"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    start_urls = ["https://www.pizzahut.com.tw/xml/store_list.xml"]

    def parse(self, response, **kwargs):
        for store in response.xpath(r"//storelist/store"):
            item = Feature()
            item["ref"] = store.xpath("./id/text()").get()
            item["name"] = store.xpath("./s_n/text()").get()
            item["state"] = store.xpath("./m_c/text()").get()
            item["city"] = store.xpath("./m_a/text()").get()
            item["addr_full"] = store.xpath("./addr/text()").get()
            item["lat"], item["lon"] = store.xpath("./latlng/text()").get().split(",", 1)
            item["phone"] = store.xpath("./ctel/text()").get()
            yield item
