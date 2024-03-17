from scrapy import Spider

from locations.items import Feature
from locations.pipelines.extract_gb_postcode import extract_gb_postcode


class TimHortonsGBSpider(Spider):
    name = "tim_hortons_gb"
    item_attributes = {"brand": "Tim Hortons", "brand_wikidata": "Q175106"}
    start_urls = ["https://timhortons.co.uk/find-a-tims"]

    def parse(self, response):
        for poi in response.xpath('//div[@class="box"]'):
            item = Feature()
            item["website"] = response.url
            item["lat"], item["lon"] = poi.xpath("@data-module-lat").get(), poi.xpath("@data-module-lng").get()
            item["ref"] = item["lat"]
            city = item["city"] = poi.xpath('.//*[@class="location-city"]/text()').get()
            details = poi.xpath('.//*[@class="location-address"]/text()').getall()
            joined_details = ",".join(details)
            if postcode := extract_gb_postcode(joined_details):
                # The postcode if present is where the address ends and the rest of the text begins.
                item["postcode"] = postcode
                dirty_address = joined_details.split(postcode)[0]
                if not city.lower() in dirty_address.lower():
                    dirty_address += "," + city
                dirty_address += "," + postcode
                item["addr_full"] = dirty_address
            yield item
