import scrapy
import json
import re
from locations.items import GeojsonPointItem


class NordstromSpider(scrapy.Spider):
    name = "nordstrom"
    item_attributes = {"brand": "Nordstrom"}
    allowed_domains = ["shop.nordstrom.com"]
    start_urls = ("https://shop.nordstrom.com/c/sitemap-stores",)
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36",
    }

    def parse_store(self, response):
        # Handle broken links e.g. Nordstrom Rack Long Beach Exchange
        if response.url == "https://shop.nordstrom.com/stores":
            return
        else:
            script_content = response.xpath(
                '//script[contains(text(), "window.__INITIAL_CONFIG__")]/text()'
            ).extract_first()
            data = json.loads(
                re.search(r"window.__INITIAL_CONFIG__ =(.*}})", script_content).group(1)
            )
            store_data = data["viewData"]["stores"]["stores"][0]

            properties = {
                "name": store_data["name"],
                "ref": store_data["number"],
                "addr_full": store_data["address"],
                "city": store_data["city"],
                "state": store_data["state"],
                "postcode": store_data["zipCode"],
                "phone": store_data.get("phone"),
                "website": store_data.get("url") or response.url,
                "lat": store_data.get("latitude"),
                "lon": store_data.get("longitude"),
            }

            yield GeojsonPointItem(**properties)

    def parse(self, response):
        urls = response.xpath('//a[contains(@href ,"store-details")]/@href').extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_store)
