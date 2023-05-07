import scrapy

from locations.structured_data_spider import StructuredDataSpider


class JustCutsSpider(StructuredDataSpider):
    name = "just_cuts"
    item_attributes = {"brand": "Just Cuts", "brand_wikidata": "Q116784479"}
    allowed_domains = ["www.justcuts.com.au"]
    start_urls = ["https://www.justcuts.com.au/salonlocator/SalonsLatLongUpdate.aspx"]
    wanted_types = ["HairSalon"]
    time_format = "%I:%M %p"

    def parse(self, response):
        for urlpath in response.xpath("//marker/@storeurl").getall():
            yield scrapy.Request(url="https://www.justcuts.com.au" + urlpath, callback=self.parse_sd)

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = response.url.split("sid=", 1)[1]
        if item["country"] == "NZ":
            item.pop("state")
        if "img/photos/store1.jpg" in item["image"]:
            item.pop("image")
        if "www.facebook.com/JustCutsSalons" in item["facebook"]:
            item.pop("facebook")
        if item["phone"] == 0:
            item.pop("phone")
        yield item
