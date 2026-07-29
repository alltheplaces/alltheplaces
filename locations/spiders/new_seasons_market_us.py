from scrapy.http import Response

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class NewSeasonsMarketUSSpider(JSONBlobSpider):
    name = "new_seasons_market_us"
    item_attributes = {"brand": "New Seasons Market", "brand_wikidata": "Q7011463"}
    start_urls = ["https://www.newseasonsmarket.com/find-a-store"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response):
        for location in response.xpath('//*[@id="store"]//*[@class="sr-list"]'):
            item = Feature()
            item["branch"] = location.xpath(".//@data-store-name").get()
            item["lat"] = location.xpath(".//@data-latitude").get()
            item["lon"] = location.xpath(".//@data-longitude").get()
            item["state"] = location.xpath(".//@data-state-name").get()
            item["ref"] = location.xpath(".//@id").get()
            item["phone"] = location.xpath('.//*[contains(@href,"tel:")]/@href').get().replace("tel:", "")
            item["street_address"] = location.xpath('.//*[@class="store-addressdetails"]/text()').get()
            item["city"] = location.xpath('.//*[@class="store-city"]/text()').get()
            item["postcode"] = location.xpath('.//*[@class="store-zipcode"]/text()').get()
            yield item
