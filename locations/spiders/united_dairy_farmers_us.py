import re

import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class UnitedDairyFarmersUSSpider(scrapy.Spider):
    download_delay = 0.2
    name = "united_dairy_farmers_us"
    item_attributes = {"brand": "United Dairy Farmers", "brand_wikidata": "Q7887677"}
    allowed_domains = ["udfinc.com"]
    start_urls = ("https://www.udfinc.com/wp-sitemap-posts-wpsl_stores-1.xml",)

    def parse(self, response):
        urls = response.xpath("//text()").extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_store)

    def parse_store(self, response):
        rawdata = response.xpath('//script[@type="text/javascript" and contains(text(), "locations")]/text()').extract()
        store_text = rawdata[0]
        json_prelim = re.search('store":(.*)', store_text).group()
        json_data = json_prelim.replace("[", "")
        json_data = json_data.replace("]", "")
        json_data = json_data.replace("'", "")
        json_data = json_data.replace("}", "")
        json_data = json_data.replace(";", "")
        json_data = json_data.replace('"', "")
        data = json_data.split(",")
        phone = response.xpath('//div[@class="wpsl-contact-details"]//*/a/@href').extract()
        try:
            properties = {
                "ref": data[9].split(":")[1],
                "name": "United Dairy Farmers",
                "addr_full": data[1].split(":")[1],
                "city": data[3].split(":")[1],
                "state": data[4].split(":")[1],
                "postcode": data[5].split(":")[1],
                "country": data[6].split(":")[1],
                "phone": phone[0].split(":")[1],
                "lat": float(data[7].split(":")[1]),
                "lon": float(data[8].split(":")[1]),
            }

        except Exception:
            properties = {
                "ref": data[9].split(":")[1],
                "name": "United Dairy Farmers",
                "addr_full": data[1].split(":")[1],
                "city": data[3].split(":")[1],
                "state": data[4].split(":")[1],
                "postcode": data[5].split(":")[1],
                "country": data[6].split(":")[1],
                "phone": "",
                "lat": float(data[7].split(":")[1]),
                "lon": float(data[8].split(":")[1]),
            }

        apply_category(Categories.FUEL_STATION, properties)
        yield Feature(**properties)
