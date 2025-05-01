import re
import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class GdkGBSpider(scrapy.Spider):
    name = "gdk_gb"
    item_attributes = {"brand": "German Doner Kebab", "brand_wikidata": "Q112913418"}
    start_urls = ["https://www.gdk.com/AJAX_LoadStores.php"]

    def parse(self, response):
        data = response.xpath("//div[contains(@class, 'location-item')]")
        for location in data:
            item = Feature()
            item["branch"] = location.xpath(".//h3//text()").get()
            item["addr_full"] = (
                location.xpath(".//a[contains(@href, 'https://www.google.com/maps/dir/Current+Location/')]//@href")
                .get()
                .replace("https://www.google.com/maps/dir/Current+Location/", "")
                .replace("\r", ",")
            )
            item["name"] = "German Doner Kebab"
            item["website"] = location.xpath(".//a[contains(@href, 'postcode')]//@href").get()
            address = item["addr_full"]
            address = re.split(r"[,\s]+", address)[-2:]
            address = " ".join(address)
            item["postcode"] = address
            item["ref"] = item["postcode"]
            apply_category(Categories.FAST_FOOD, item)
            yield item
