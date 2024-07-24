from scrapy import Request, Spider, Selector

from locations.google_url import url_to_coords
from locations.items import Feature

class MinimartBGSpider(Spider):
    name = "minimart_bg"
    item_attributes = {"brand": "Minimart", "brand_wikidata": "Q119168386"}
    allowed_domains = ["mini-mart.bg", "goo.gl"]
    start_urls = ["https://mini-mart.bg/nameri-magazin"]
    custom_settings = {"ROBOTSTXT_OBEY": False}  # Ignore www.google.com robots.txt
    no_refs = True

    def parse(self, response):
        locations = response.xpath("//div[contains(@class, 'et_pb_with_border')]").getall()
        for location in locations:
            htmlLocation = Selector(text=location)
            item = Feature()
            item["addr_full"] = htmlLocation.xpath(".//p//text()").get()
            location_url = htmlLocation.xpath(".//a/@href").get()
            if location_url is not None:
                yield Request(url=location_url, meta={"item": item}, callback=self.parse_maps_url)

    # Follow shortened URL to find full Google Maps URL containing coordinates
    def parse_maps_url(self, response):
        item = response.meta["item"]
        item["lat"], item["lon"] = url_to_coords(response.url)
        yield item
