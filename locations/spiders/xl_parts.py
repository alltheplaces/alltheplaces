import re

import scrapy

from locations.items import Feature


class XlPartsSpider(scrapy.Spider):
    name = "xl_parts"
    item_attributes = {"brand": "XL Parts", "brand_wikidata": "Q123188576", "country": "US"}
    allowed_domains = ["www.xlparts.com"]

    def start_requests(self):
        url = "https://www.xlparts.com/en/locations"

        yield scrapy.http.FormRequest(url=url, method="POST", callback=self.parse)

    def parse(self, response):
        stores = response.xpath('//div[contains(@id, "store")]')
        script_data = response.xpath('//script[contains(text(), "var map")]').extract_first()

        for store in stores:
            item = Feature()
            store_div = store.xpath("./@id").extract_first()
            item["ref"] = re.search(r"store_div_([0-9]*)", store_div).group(1)
            item["name"] = store.xpath("./h3/text()").extract_first().strip()
            item["addr_full"] = ", ".join(store.xpath("./ul/li/text()").getall())
            item["phone"] = store.xpath("./ul/li/span/text()").extract_first()

            # Fetch the coordinates
            pattern = rf"""data\['storeID'\] \= "{store_div}"\;.*?var lat\=([0-9.]*);.*?var longtd=([0-9.-]*);"""
            if m := re.search(pattern, script_data, flags=re.MULTILINE | re.DOTALL):
                item["lat"], item["lon"] = m.groups()

            yield item
