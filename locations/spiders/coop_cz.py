import re

from scrapy import Request, Spider

from locations.categories import Categories, apply_category
from locations.items import Feature


class CoopCZSpider(Spider):
    name = "coop_cz"
    item_attributes = {"brand": "COOP", "brand_wikidata": "Q52851660"}
    start_urls = [
        "https://www.skupina.coop/cooperative/list/",
    ]

    def parse(self, response):
        for location_url in response.xpath("//a[@class='button']/@href").getall():
            location_url = response.urljoin(location_url)
            yield Request(url=location_url, callback=self.parse_cooperative)

    def parse_cooperative(self, response):
        for location in response.xpath("//div[contains(@class, 'obsah')]/table/tbody/tr"):
            relative_url = location.xpath("./td[1]/a/@href").get()
            store = {}
            store["ref"] = relative_url.removeprefix("/")
            store["website"] = response.urljoin(relative_url)
            store["city"] = location.xpath("./td[2]/text()").get()
            store["postcode"] = location.xpath("./td[4]/text()").get()
            apply_category(Categories.SHOP_SUPERMARKET, store)
            yield Request(url=store["website"], callback=self.parse_location, cb_kwargs={"store": store})

    def parse_location(self, response, store):
        lat_lon_regex = re.compile(r"new google\.maps\.LatLng\(\"(-?\d+\.\d+)\", \"(-?\d+\.\d+)\"\)")
        if match := re.search(lat_lon_regex, response.text):
            store["lat"] = float(match.group(1))
            store["lon"] = float(match.group(2))

        contacts = response.xpath("//*[contains(@class, 'kontakt')]")
        if phone := contacts.xpath("//*[contains(@class, 'telefon')]//text()").get():
            store["phone"] = phone
        if email := contacts.xpath("//*[contains(@class, 'mail')]//text()").get():
            store["email"] = email
        # override website if location explicitly provides its own
        if website := contacts.xpath("//*[contains(@class, 'link')]//a/@href").get():
            store["website"] = website

        yield Feature(**store)
