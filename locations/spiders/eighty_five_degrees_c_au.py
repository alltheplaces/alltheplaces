from scrapy import Spider

from locations.google_url import extract_google_position
from locations.items import Feature


class EightyFiveDegreesCAUSpider(Spider):
    name = "eighty_five_degrees_c_au"
    item_attributes = {"brand": "85°C", "brand_wikidata": "Q4644852"}
    start_urls = ["https://www.85cafe.com.au/store-finder/"]

    def parse(self, response):
        for store in response.xpath("//div[@class='card mb-2']"):
            item = Feature()
            item["website"] = store.xpath(".//h2/a/@href").get()
            item["ref"] = item["website"].split("/")[-1]
            item["branch"] = store.xpath(".//h2/a/text()").get().removeprefix("85C Daily Cafe ")
            item["addr_full"] = store.xpath("string(.//address/p[1])").get()
            item["phone"] = store.xpath("string(.//address/p[2])").get()
            extract_google_position(item, store)
            yield item
