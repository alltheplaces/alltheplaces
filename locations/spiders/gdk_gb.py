import re
import scrapy

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class GdkGBSpider(scrapy.Spider):
    name = "gdk_gb"
    item_attributes = {"brand": "German Doner Kebab", "brand_wikidata": "Q112913418"}
    start_urls = ["https://www.gdk.com/AJAX_LoadStores.php"]

    def parse(self, response):
        data = response.xpath("//div[contains(@class, 'location-item')]")
        for location in data:
            item = Feature()
            item["branch"] = location.xpath("//h3//text()").get()
            item["addr_full"] = location.xpath("//a[contains(@href, 'https://www.google.com/maps/dir/Current+Location/')]//@href").get().replace("https://www.google.com/maps/dir/Current+Location/","").replace("\r",",")
            item["name"] = "German Doner Kebab"
            item["website"] = location.xpath("//a[contains(@href, 'postcode')]//@href").get()
            item["postcode"] = item["website"].replace("https://www.order.gdk.com/takeaway/selectstore.php?auto=1&postcode=","")
            item["ref"] = item["postcode"]
            yield item
