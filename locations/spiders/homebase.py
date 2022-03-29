import scrapy
import re
import json
from locations.items import GeojsonPointItem


class ArgosSpider(scrapy.Spider):

    name = "homebase"
    item_attributes = {"brand": "Homebase"}
    allowed_domains = ["www.homebase.co.uk"]
    download_delay = 0.5
    start_urls = ("https://www.homebase.co.uk/stores",)

    def parse_stores(self, response):
        data = re.findall(
            r"var com_bunnings_locations_mapLocations = [^;]+",
            response.text,
        )
        json_data = json.loads(
            data[0].replace("var com_bunnings_locations_mapLocations = ", "")
        )
        properties = {
            "addr_full": json_data[0]["Store"]["Address"]["Address"]
            + json_data[0]["Store"]["Address"]["AddressLineTwo"],
            "phone": json_data[0]["Store"]["Phone"],
            "city": json_data[0]["Store"]["Address"]["Suburb"],
            "state": json_data[0]["Store"]["Address"]["State"],
            "postcode": json_data[0]["Store"]["Address"]["Postcode"],
            "country": json_data[0]["Store"]["Address"]["Country"],
            "ref": json_data[0]["Store"]["StoreID"],
            "website": response.url,
            "lat": float(json_data[0]["Store"]["Location"]["Latitude"]),
            "lon": float(json_data[0]["Store"]["Location"]["Longitude"]),
        }

        hours = response.xpath('//time[@itemprop="openingHours"]/@datatime').extract()
        if hours != []:
            properties["opening_hours"] = "; ".join(x for x in hours)

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        urls = response.xpath(
            '//div[@class="store-listing__state__list alpha"]/ul/li/a/@href'
        ).extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)
