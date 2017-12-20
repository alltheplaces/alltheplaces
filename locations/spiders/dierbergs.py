import json
import re
import scrapy
from locations.items import GeojsonPointItem

class DierbergsSpider(scrapy.Spider):
    name = "dierbergs"
    allowed_domains = ["www.dierbergs.com"]

    start_urls = (
        'http://www.dierbergs.com/MyDierbergs/Locations',
    )

    def parse_Ref(self, data):
        data = data.xpath(".//img")[0]
        ref = data.xpath("@alt").extract_first()
        match = re.search(r'Store #(\d{1,})', ref)
        ref = match.groups()[0]
        return ref

    def parse(self, response):
        data = response.xpath('.//div[@class="location-listing-item row"]')

        for store in data:
            ref = self.parse_Ref(store)
            properties = {
                'ref': ref,
                'addr_full': store.xpath("//span[@class='address']//text()").extract_first().strip(),
                'city': store.xpath("//span[@class='city']//text()").extract_first().strip(),
                'state': store.xpath("//span[@class='state']//text()").extract_first().strip(),
                'postcode': store.xpath("//span[@class='zip']//text()").extract_first().strip(),
                'phone': store.xpath("//span[@class='phone']//text()").extract_first().strip(),
                'name': store.xpath(".//strong//text()").extract_first().strip(),
                'lon': store.xpath("@data-lon").extract_first(),
                'lat': store.xpath("@data-lat").extract_first()
            }

            yield GeojsonPointItem(**properties)
            
