import scrapy

from locations.google_url import url_to_coords
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class LagkagehusetDKSpider(scrapy.Spider):
    name = "lagkagehuset_dk"
    item_attributes = {"brand": "Lagkagehuset", "brand_wikidata": "Q12323572"}
    start_urls = ["https://lagkagehuset.dk/butikker"]
    no_refs = True

    def parse(self, response, **kwargs):
        for store in response.xpath("//*[@region]"):
            item = Feature()
            item["name"] = store.xpath('.//*[@class="store-headline"]/text()').get()
            item["addr_full"] = merge_address_lines(store.xpath('.//*[@class="store-content"]/p[1]/text()').getall())
            if map_url := store.xpath(".//a[contains(@href, 'google')]/@href").get():
                item["lat"], item["lon"] = url_to_coords(map_url.replace("google.dk", "google.com"))
            item["email"] = store.xpath('.//a[contains(@href, "mailto")]/text()').get()
            item["phone"] = store.xpath('.//a[contains(@href, "tel")]/text()').get()
            yield item
