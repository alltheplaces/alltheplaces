from scrapy import Spider

from locations.items import Feature


class UniversalStoreAUSpider(Spider):
    name = "universal_store_au"
    item_attributes = {"brand": "Universal Store", "brand_wikidata": "Q96412731"}
    allowed_domains = ["www.universalstore.com"]
    start_urls = ["https://www.universalstore.com/stores/"]

    def parse(self, response):
        for location_html in response.xpath('//div[@class="store-list"]/div'):
            properties = {
                "ref": location_html.xpath(".//@data-store-number").get(),
                "name": location_html.xpath(".//@data-centre-name").get(),
                "lat": location_html.xpath(".//@data-coords").get().split(",", 1)[0].strip(),
                "lon": location_html.xpath(".//@data-coords").get().split(",", 1)[1].strip(),
                "addr_full": location_html.xpath(".//@data-address").get(),
                "state": location_html.xpath(".//@data-state").get(),
                "phone": location_html.xpath('.//span[@class="phoneFormatted"]/text()').get().strip(),
                "website": "https://www.universalstore.com" + location_html.xpath(".//a/@href").get(),
            }
            if "Perfect Stranger" in properties["name"]:
                properties["brand"] = "Perfect Stranger"
                properties["brand_wikidata"] = "Q119444659"
            yield Feature(**properties)
