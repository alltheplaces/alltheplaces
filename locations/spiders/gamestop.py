# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem


class GamestopSpider(scrapy.Spider):
    name = "gamestop"
    item_attributes = {"brand": "GameStop"}
    allowed_domains = ["www.gamestop.com"]
    start_urls = (
        "https://spatial.virtualearth.net/REST/v1/data/8f92e4701aa94bbba485642dc6d15873/_AllStores/StoreSchema?s=1&$format=json&callback=getStoreInfoSuccess&spatialFilter=&$filter=DisplayType%20Eq%20%271%27%20and%20StoreName%20Ne%20%27GameStop.com%27%20and%20StoreName%20Ne%20%27Internet%20/%20Stores%27%20and%20StoreName%20Ne%20%27GameStop%20Military%27&key=AleEo0hykwhhc2_vhIDzSZvfqbcmdTVzwZp3TrNliPr6CPJtxveXCdwIr7zAHu2O&$top=250&callback=jQuery111105958918103101543_1513486119155&_=1513486119161",
    )

    def parseAddr(self, addr1, addr2):
        if addr2 == "":
            return addr1
        else:
            return addr1 + ", " + addr2

    def parse(self, response):
        # retrieve JSON data from REST endpoint
        # items = response.xpath('//text()').extract()

        # convert data variable from unicode to string
        # items = str(items)

        # convert type string representation of list to type list
        # data = [items]

        # load list into json object for parsing
        jsondata = response.json()

        # iterate items
        for item in jsondata["d"]["results"]:
            yield GeojsonPointItem(
                ref=item["EntityID"],
                lat=float(item["Latitude"]),
                lon=float(item["Longitude"]),
                addr_full=self.parseAddr(item["Address1"], item["Address2"]),
                city=item["Locality"],
                state=item["AdminDistrict"],
                postcode=item["PostalCode"],
                name=item["MallName"],
                phone=item["Phone"],
                opening_hours=item["StoreHours"],
            )
