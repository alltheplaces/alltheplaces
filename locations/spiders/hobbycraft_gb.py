import scrapy

from locations.structured_data_spider import StructuredDataSpider


class HobbycraftGBSpider(StructuredDataSpider):
    name = "hobbycraft_gb"
    item_attributes = {"brand": "Hobbycraft", "brand_wikidata": "Q16984508"}
    start_urls = ["https://www.hobbycraft.co.uk/storelist/"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item.pop("facebook", None)
        item.pop("image", None)
        item.pop("twitter", None)
        yield item

    def parse(self, response):
        for link in response.xpath('//a[contains(@href, "/stores/")]/@href').getall():
            yield scrapy.Request(url=response.urljoin(link), callback=self.parse_sd)
