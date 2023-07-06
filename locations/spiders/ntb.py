import urllib

import scrapy

from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


class NtbSpider(scrapy.Spider):
    name = "ntb"
    item_attributes = {
        "brand": "National Tire and Battery",
        "brand_wikidata": "Q6978944",
    }
    allowed_domains = ["ntb.com"]
    download_delay = 0.25
    start_urls = [
        "https://www.ntb.com/storelocator/allstores?__escaped_fragment__",
    ]

    def parse(self, response):
        for link in response.follow_all(
            css='[ng-repeat="store in allStoresVm.activeStoreList"] a',
            callback=self.parse_store,
        ):
            yield link.replace(url=link.url + "?__escaped_fragment__")

    def parse_store(self, response):
        MicrodataParser.convert_to_json_ld(response)
        item = LinkedDataParser.parse(response, "AutomotiveBusiness")
        if item is None:
            return
        url = response.xpath('//link[@rel="canonical"]/@href').get()
        item["website"] = url
        item["ref"] = url.split("/")[-2]

        latlon = response.xpath('//a/@href[contains(.,"?latitude=")]').get()
        qs = urllib.parse.parse_qs(urllib.parse.urlsplit(latlon).query)
        [item["lat"]] = qs["latitude"]
        [item["lon"]] = qs["longitude"]
        yield item
