import scrapy

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT

AMENITIES_MAPPING = {
    "10": Extras.CAR_WASH,
    "12": Fuel.DIESEL,
    "13": Fuel.CNG,
    "14": Fuel.LNG,
    "15": Fuel.ADBLUE,
    "16": Fuel.E85,
}
# Sells Gas = 11, but it's not clear what octane number to use.


class KwikTripSpider(scrapy.Spider):
    name = "kwiktrip"
    item_attributes = {"brand": "Kwik Trip", "brand_wikidata": "Q6450420"}
    allowed_domains = ["www.kwiktrip.com"]
    download_delay = 0
    user_agent = BROWSER_DEFAULT
    start_urls = ["https://www.kwiktrip.com/Maps-Downloads/Store-List"]
    requires_proxy = True

    def parse(self, response):
        rows = response.xpath("(//tr)[position()>1]")  # Skip header of table

        for row in rows:
            properties = {
                "ref": row.xpath('.//td[@class="column-1"]/text()').extract_first(),
                "name": row.xpath('.//td[@class="column-2"]/text()').extract_first(),
                "street_address": row.xpath('.//td[@class="column-3"]/text()').extract_first(),
                "city": row.xpath('.//td[@class="column-4"]/text()').extract_first(),
                "state": row.xpath('.//td[@class="column-5"]/text()').extract_first(),
                "postcode": row.xpath('.//td[@class="column-6"]/text()').extract_first(),
                "lat": row.xpath('.//td[@class="column-8"]/text()').extract_first(),
                "lon": row.xpath('.//td[@class="column-9"]/text()').extract_first(),
                "phone": row.xpath('.//td[@class="column-7"]/text()').extract_first(),
                "website": response.url,
            }
            item = Feature(**properties)

            for amenity in AMENITIES_MAPPING:
                if row.xpath(f'.//td[@class="column-{amenity}"]/text()').extract_first() == "Yes":
                    apply_yes_no(AMENITIES_MAPPING.get(amenity), item, True)

            apply_category(Categories.FUEL_STATION, item)

            yield item
