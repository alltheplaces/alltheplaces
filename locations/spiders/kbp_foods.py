import scrapy
from scrapy import Selector

from locations.items import Feature


class KbpFoodsSpider(scrapy.Spider):
    name = "kbp_foods"
    item_attributes = {"brand": "KBP Foods"}

    def make_request(self, page: int):
        brand_url = "https://kbp-foods.com/wp-json/facetwp/v1/refresh"
        payload = f'{{"action":"facetwp_refresh","data":{{"facets":{{"proximity":[],"map":[]}},"template":"locations","paged":{page}}}}}'
        return scrapy.Request(url=brand_url, body=payload, method="POST", cb_kwargs={"page": page})

    def start_requests(self):
        yield self.make_request(1)

    def parse(self, response, **kwargs):
        if data := response.json()["settings"]["map"]["locations"]:
            for store in data:
                item = Feature()
                html_data = Selector(text=store["content"])
                item["ref"] = store["post_id"]
                item["lat"] = store["position"]["lat"]
                item["lon"] = store["position"]["lng"]
                item["name"] = "KBP Foods"
                item["branch"] = html_data.xpath("//h2/text()").get()
                item["addr_full"] = html_data.xpath('//*[@class="fwpl-item"]/text()').get()
                item["phone"] = html_data.xpath('//*[contains(@href,"tel:")]/text()').get()
                item["website"] = "https://kbp-foods.com/"
                yield item
            yield self.make_request(kwargs["page"] + 1)
