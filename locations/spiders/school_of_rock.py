import scrapy

from locations.structured_data_spider import StructuredDataSpider


class SchoolOfRockSpider(StructuredDataSpider):
    name = "school_of_rock"
    item_attributes = {"brand": "School of Rock", "brand_wikidata": "Q7756376"}
    allowed_domains = [
        "www.schoolofrock.com",
        "www.schoolofrock.com.br",
        "www.schoolofrock.es",
        "www.schoolofrock.com.pt",
        "www.schoolofrock.com.tw",
    ]
    start_urls = ["https://www.schoolofrock.com/locations"]
    json_parser = "chompjs"
    search_for_image = False
    search_for_twitter = False
    search_for_instagram = True

    def parse(self, response):
        for location in response.xpath('.//a[@class="locations-list__city"]/@href').getall():
            yield scrapy.Request(url=location, callback=self.parse_sd)

    def post_process_item(self, item, response, ld_data):
        item.pop("image")
        yield item
