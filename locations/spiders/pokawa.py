from scrapy import Spider

from locations.items import Feature


class PokawaSpider(Spider):
    name = "pokawa"
    item_attributes = {"brand": "Pokawa", "brand_wikidata": "Q123018553"}
    start_urls = ["https://restaurants.pokawa.com/wp-content/plugins/superstorefinder-wp/ssf-wp-xml.php"]

    def parse(self, response, **kwargs):
        for location in response.xpath("/locator/store/item"):
            item = Feature()
            item["name"] = location.xpath("location/text()").get()
            item["addr_full"] = location.xpath("address/text()").get()
            item["lat"] = location.xpath("latitude/text()").get()
            item["lon"] = location.xpath("longitude/text()").get()
            item["website"] = location.xpath("exturl/text()").get()
            item["ref"] = location.xpath("storeId/text()").get()
            item["country"] = location.xpath("country/text()").get()
            item["image"] = location.xpath("storeimage/text()").get()

            yield item
