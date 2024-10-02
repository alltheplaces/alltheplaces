from scrapy import Spider

from locations.google_url import extract_google_position
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address

SAE_INSTITUTE_SHARED_ATTRIBUTES = {"brand": "SAE Institute", "brand_wikidata": "Q201438"}


# Also used by UK, US
class SaeInstitueAUSpider(Spider):
    name = "sae_institute_au"
    start_urls = ["https://sae.edu.au/contact-us/"]
    item_attributes = SAE_INSTITUTE_SHARED_ATTRIBUTES

    def parse(self, response):
        for location in response.xpath('.//div[@class="location_tile_item-container"]'):
            item = Feature()

            item["branch"] = location.xpath(".//h5/text()").get()
            extract_google_position(item, location)

            item["addr_full"] = clean_address(
                location.xpath('.//span[@class="location_tile_item-text"]/text()').getall()
            )
            if item["addr_full"] == "":
                item["addr_full"] = clean_address(
                    location.xpath('.//span[@class="location_tile_item-text"]/span/text()').getall()
                )

            item["housenumber"] = location.xpath('.//span[@class="segment-street_number"]/text()').get()
            item["street"] = location.xpath('.//span[@class="segment-street_name"]/text()').get()
            item["city"] = location.xpath('.//span[@class="segment-city"]/text()').get()
            item["state"] = location.xpath('.//span[@class="segment-state_short"]/text()').get()
            item["postcode"] = location.xpath('.//span[@class="segment-post_code"]/text()').get()

            item["website"] = location.xpath('.//div[@class="location_tile_item-cta"]/a/@href').get()
            item["ref"] = item["website"]
            # All have the same phone, so not extracting
            # Email is protected
            yield from self.post_process_item(item, response, location)

    def post_process_item(self, item, response, location):
        # Post processing as needed by other countries
        yield item
