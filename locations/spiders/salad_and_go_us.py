from scrapy import Spider

from locations.categories import Extras, apply_yes_no
from locations.items import Feature


class SaladAndGoUSSpider(Spider):
    name = "salad_and_go_us"
    item_attributes = {"brand": "Salad and Go", "brand_wikidata": "Q110127908"}
    start_urls = ["https://www.saladandgo.com/locations/"]

    def parse(self, response, **kwargs):
        for location in response.xpath('//div[@class="marker"]'):
            item = Feature()

            item["name"] = location.xpath("@data-name").get()
            item["addr_full"] = location.xpath("@data-address").get()
            item["lat"] = location.xpath("@data-lat").get()
            item["lon"] = location.xpath("@data-lng").get()
            item["ref"] = item["website"] = location.xpath("@data-link").get()
            apply_yes_no(Extras.DRIVE_THROUGH, item, location.xpath("@data-drivethru").get() == "1")

            yield item
