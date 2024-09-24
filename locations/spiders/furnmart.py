import re
from urllib.parse import urlparse

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class FurnmartSpider(Spider):
    name = "furnmart"
    start_urls = [
        "https://www.furnmart.co.bw/StoreLocator/SearchShops",
        "https://www.furnmart.com.na/StoreLocator/SearchShops",
        "https://www.furnmart.co.za/StoreLocator/SearchShops",
    ]
    item_attributes = {
        "brand": "Furnmart",
        "brand_wikidata": "Q118185771",
    }

    def start_requests(self):
        for url in self.start_urls:
            yield from self.request_page(url, 1)

    def request_page(self, url, page):
        yield JsonRequest(
            url=url,
            data={
                "latitude": "",
                "longitude": "",
                "radius": "100",
                "tag": "",
                "sortBy": "10",
                "pageNumber": page,
            },
            meta={"url": url, "page": page},
        )

    def parse(self, response):
        for location in response.xpath('.//li[@class="shops-item visible"]'):
            item = Feature()
            item["lat"] = location.xpath(".//a/@data-latitude").get()
            item["lon"] = location.xpath(".//a/@data-longitude").get()
            item["branch"] = location.xpath(".//@title").get()
            item["website"] = (
                urlparse(response.url)._replace(path=location.xpath('.//a[@class="shop-link"]/@href').get()).geturl()
            )
            # item["ref"] = location.xpath('@data-shopid').get() # May not be unique across countries
            item["ref"] = item["website"]
            description_raw = location.xpath('.//div[@class="short-description"]').get()
            description = [line.strip() for line in re.sub(r"<\/?[^b].*?>", " ", description_raw).split("<br>")]
            if any(["Phone:" in line for line in description]):
                phone_raw = [line for line in description if "Phone:" in line][0]
                item["phone"] = phone_raw.replace("Phone:", "")
                description.remove(phone_raw)
            item["addr_full"] = clean_address(description)
            yield item

        if len(response.xpath('.//li[@class="shops-item visible"]')) == 20:
            yield from self.request_page(response.meta["url"], response.meta["page"] + 1)
