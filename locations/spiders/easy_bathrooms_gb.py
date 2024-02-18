from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.items import Feature


class EasyBathroomsGBSpider(CrawlSpider):
    name = "easy_bathrooms_gb"
    item_attributes = {
        "brand": "Easy Bathrooms",
        "brand_wikidata": "Q114348566",
        "extras": Categories.SHOP_BATHROOM_FURNISHING.value,
    }
    allowed_domains = ["www.easybathrooms.com"]
    start_urls = ["https://www.easybathrooms.com/our-showrooms"]
    rules = [Rule(LinkExtractor(allow=r"^https:\/\/www\.easybathrooms\.com\/our-showrooms\/[^/]+$"), callback="parse")]

    def parse(self, response):
        js_blob = response.xpath('//script[contains(text(), "function initMap()")]/text()').get()
        lat, lon = js_blob.split("google.maps.LatLng(", 1)[1].split(")", 1)[0].split(", ", 1)
        address_details = response.xpath('//main[@id="main-content"]/div[1]/div[1]/div[2]/div[1]')
        contact_details = response.xpath('//main[@id="main-content"]/div[5]/div[2]/ul[1]')
        properties = {
            "ref": response.url.split("/(?!$)")[-1],
            "name": address_details.xpath("./h1/text()").get(),
            "lat": lat,
            "lon": lon,
            "addr_full": ", ".join(
                filter(None, map(str.strip, address_details.xpath("./div[2]/ul/li/text()").getall()))
            ),
            "phone": contact_details.xpath("./li[2]/span/text()").get(),
            "email": response.xpath('//select[@id="collection_store"]/option[@selected]/@value').get(),
            "website": response.url,
        }
        hours_string = " ".join(
            filter(None, map(str.strip, response.xpath('//div[@id="opening-times"]/ul[1]//text()').getall()))
        )
        properties["opening_hours"] = OpeningHours()
        properties["opening_hours"].add_ranges_from_string(hours_string)
        yield Feature(**properties)
