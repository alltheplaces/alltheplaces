from urllib.parse import urljoin

from scrapy import FormRequest, Selector, Spider

from locations.items import Feature


class InterparkingBESpider(Spider):
    name = "interparking_be"
    item_attributes = {"brand": "Interparking", "brand_wikidata": "Q1895863"}

    def start_requests(self):
        yield FormRequest(
            url="https://www.interparking.be/en/find-parking/search-results/?keyword=",
            formdata={"urlHash": "{}", "requestType": "FilterParkings"},
        )

    def parse(self, response, **kwargs):
        for location in response.json()["MapItems"]:
            item = Feature()
            item["lat"], item["lon"] = location["Point"]
            item["ref"] = location["Id"]

            sel = Selector(text=location["Html"])

            item["website"] = urljoin(response.url, sel.xpath('//a[@class="link"]/@href').get())
            item["image"] = urljoin(response.url, sel.xpath("//img/@src").get())
            item["addr_full"] = sel.xpath("//p/text()").get()
            item["name"] = sel.xpath("//strong/text()").get()

            yield item
