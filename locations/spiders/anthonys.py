import scrapy

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.structured_data_spider import extract_phone


class AnthonysSpider(scrapy.Spider):
    name = "anthonys"
    item_attributes = {"brand": "Anthony's Coal Fired Pizza", "brand_wikidata": "Q117536208", "country": "US"}
    start_urls = ["https://acfp.com/locations/"]

    def parse(self, response):
        for store in response.xpath('//*[@class="location"]'):
            item = Feature()
            item["ref"] = item["website"] = response.urljoin(
                store.xpath('.//a[contains(@href,"locations")]/@href').get("")
            )
            item["lat"] = store.xpath(".//@data-lat").get()
            item["lon"] = store.xpath(".//@data-lng").get()
            item["addr_full"] = merge_address_lines(store.xpath('.//*[@class="location-address"]/p/text()').getall())
            extract_phone(item, store)
            yield item
