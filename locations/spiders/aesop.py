from typing import Iterable

from scrapy.http import Request

from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider
from locations.user_agents import BROWSER_DEFAULT


class AesopSpider(JSONBlobSpider):
    name = "aesop"
    item_attributes = {"brand": "Aesop", "brand_wikidata": "Q4688560"}
    allowed_domains = ["www.aesop.com"]
    #start_urls = ['https://www.aesop.com/gql?operationName=storesQuery&variables={"geoPoints":"-89.999,-179.999,89.999,179.999"}&extensions={"persistedQuery":{"version":1,"sha256Hash":"d42ab0eadcbd3cc7544d7d89dfce2421455e4fe8536405878c3a17774f9f7e13"}}']
    start_urls = ['https://www.aesop.com/gql?operationName=storesQuery&variables=%7B%22geoPoints%22%3A%22-89.999%2C-179.999%2C89.999%2C179.999%22%7D&extensions=%7B%22persistedQuery%22%3A%7B%22version%22%3A1%2C%22sha256Hash%22%3A%22d42ab0eadcbd3cc7544d7d89dfce2421455e4fe8536405878c3a17774f9f7e13%22%7D%7D']
    locations_key = ["data", "stores"]
    user_agent = BROWSER_DEFAULT
    requires_proxy = True  # Akamai Bot Manager in use

    def start_requests(self) -> Iterable[Request]:
        headers = {
            "x-api-key": "VcudnZllvv2HJ0MAcV7M556XBaiIcsce3HxQC7iJ",
            "x-locale": "en-AU",
        }
        yield Request(url=self.start_urls[0], headers=headers)
