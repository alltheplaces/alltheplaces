import scrapy

from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


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

            yield Feature(**properties)
