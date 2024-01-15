from urllib.parse import urljoin

from scrapy import FormRequest, Selector, Spider

from locations.items import Feature


class InterparkingSpider(Spider):
    name = "interparking"
    item_attributes = {"brand": "Interparking", "brand_wikidata": "Q1895863"}
    countries = ["be", "fr", "fr", "it", "nl", "pl", "ro", "es"]

    def start_requests(self):
        for country in self.countries:
            yield FormRequest(
                url=f"https://www.interparking.{country}/en/find-parking/search-results/?keyword=",
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
