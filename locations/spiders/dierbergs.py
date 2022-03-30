import re
import scrapy
from locations.items import GeojsonPointItem


class DierbergsSpider(scrapy.Spider):
    download_delay = 0.2
    name = "dierbergs"
    item_attributes = {"brand": "Dierberg's"}
    allowed_domains = ["www.dierbergs.com"]

    def parse(self, response):
        data = response.xpath('.//div[@class="location-listing-item row"]')
        base_url = "http://www.dierbergs.com"

        for store in data:
            properties = {
                "ref": store.xpath(".//strong//text()").extract_first().strip(),
                "addr_full": store.xpath(".//span[@class='address']//text()")
                .extract_first()
                .strip(),
                "city": store.xpath(".//span[@class='city']//text()")
                .extract_first()
                .strip(),
                "state": store.xpath(".//span[@class='state']//text()")
                .extract_first()
                .strip(),
                "postcode": store.xpath(".//span[@class='zip']//text()")
                .extract_first()
                .strip(),
                "phone": store.xpath(".//span[@class='phone']//a//text()")
                .extract_first()
                .strip(),
                "lon": store.xpath("@data-lon").extract_first(),
                "lat": store.xpath("@data-lat").extract_first(),
                "website": base_url
                + store.xpath(".//a[@target='_top']//@href").extract_first(),
            }

            yield GeojsonPointItem(**properties)
