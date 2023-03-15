import html

from scrapy import Request, Spider

from locations.hours import OpeningHours
from locations.items import Feature


class ChoicesFlooringNZSpider(Spider):
    name = "choices_flooring_nz"
    item_attributes = {"brand": "Choices Flooring", "brand_wikidata": "Q117155570"}
    allowed_domains = ["www.choicesflooring.co.nz"]
    start_urls = ["https://www.choicesflooring.co.nz/stores/new%20zealand"]

    def parse(self, response):
        images = response.xpath('//a[contains(@class, "store_imageNZ")]')
        for image in images:
            store_url = "https://www.choicesflooring.co.nz" + image.xpath('@href').get()
            image_url = "https://www.choicesflooring.co.nz" + ((image.xpath('@style').get().split("background-image: url('", 1))[1].split("');", 1))[0]
            yield Request(url=store_url, meta={"image": image_url}, callback=self.parse_store)

    def parse_store(self, response):
        properties = {
            "ref": response.xpath('//input[@id="hdnQuoteStoreId"]/@value').get(),
            "name": response.xpath('//div[contains(@class, "st__address")]/h2/text()').get(),
            "addr_full": response.xpath('//div[contains(@class, "st__address")]/address/text()').get(),
            "phone": response.xpath('//div[contains(@class, "st__address")]/span[contains(@class, "phone")]/text()').get().replace("Phone: ", ""),
            "website": response.url,
            "image": response.meta["image"],
        }

        coords_js = response.xpath('//div[contains(@class, "st-address-hours__right")]/script[1]/text()').get()
        lat_lon = coords_js.split("google.maps.LatLng(", 1)[1].split(")", 1)[0]
        properties["lat"] = lat_lon.split(", ", 1)[0]
        properties["lon"] = lat_lon.split(", ", 1)[1]

        properties["opening_hours"] = OpeningHours()
        hours_raw = response.xpath('//div[contains(@class, "st__hours-inner")]//text()').getall()
        hours_string = html.unescape(" ".join(hours_raw))
        properties["opening_hours"].add_ranges_from_string(hours_string)
        
        yield Feature(**properties)
