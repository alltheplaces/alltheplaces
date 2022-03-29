import scrapy
import re
import lxml
from locations.items import GeojsonPointItem


class AnatomieSpider(scrapy.Spider):

    name = "anatomie"
    item_attributes = {"brand": "Anatomie"}
    allowed_domains = ["stores.boldapps.net"]
    start_urls = (
        "https://stores.boldapps.net/front-end/get_surrounding_stores.php?shop=anatomie-store.myshopify.com&latitude=38.331258&longitude=-121.54841799999997&max_distance=100000&limit=10000&calc_distance=1",
    )

    def parse(self, response):
        json_data = response.json()
        for item in json_data["stores"]:
            address = lxml.html.fromstring(item["summary"])
            properties = {
                "addr_full": address.xpath(
                    'normalize-space(.//span[@class="address"]/text())'
                ),
                "phone": "",
                "name": address.xpath('normalize-space(.//span[@class="name"]/text())'),
                "city": address.xpath('normalize-space(.//span[@class="city"]/text())'),
                "state": address.xpath(
                    'normalize-space(.//span[@class="prov_state"]/text())'
                ),
                "postcode": address.xpath(
                    'normalize-space(.//span[@class="postal_zip"]/text())'
                ),
                "ref": item["store_id"],
                "website": response.url,
                "lat": float(item["lat"]),
                "lon": float(item["lng"]),
            }
            yield GeojsonPointItem(**properties)
