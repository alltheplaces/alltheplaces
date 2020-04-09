import scrapy
import re
from locations.items import GeojsonPointItem


class ArgosSpider(scrapy.Spider):

    name = "boots"
    item_attributes = {'brand': "Boots"}
    allowed_domains = ["www.boots.com"]
    download_delay = 0.5
    start_urls = (
        'http://www.boots.com/store-a-z',
    )

    def parse_hours(self, lis):
        hours = []
        for li in lis:
            day = li.xpath('normalize-space(./td[@class="store_hours_day"]/text())').extract_first()
            times = li.xpath('normalize-space(./td[@class="store_hours_time"]/text())').extract_first()
            if times and day:
                hours.append(day[:2] + ' ' + times)

        return "; ".join(hours)

    def parse_stores(self, response):
        addr_full = response.xpath('//section[@class="store_details_content rowContainer"]/dl[@class="store_info_list"][1]/dd[@class="store_info_list_item"]/text()').extract()
        address = " ".join(map(str.strip, addr_full))
        # Handle blank store pages e.g. https://www.boots.com/stores/2250-alnwick-paikes-street-ne66-1hx
        if len(address) == 0:
            return

        slug = re.search(r'.+/(.+?)/?(?:\.html|$)', response.url).group(1)
        store_number = re.search(r'^([0-9]+)-', slug).group(1)

        properties = {
            'ref': store_number,
            'addr_full': address,
            'phone': response.xpath('//section[@class="store_details_content rowContainer"]/dl[@class="store_info_list"][3]/dd[@class="store_info_list_item"]/a/text()').extract_first(),
            'country': 'GB',
            'website': response.url,
            'lat': response.xpath('normalize-space(//input[@id="lat"]/@value)').extract_first(),
            'lon': response.xpath('normalize-space(//input[@id="lon"]/@value)').extract_first(),
        }
        hours = self.parse_hours(response.xpath('//div[@class="row store_all_opening_hours"]/div[1]/table[@class="store_opening_hours "]/tbody/tr'))
        if hours:
            properties['opening_hours'] = hours
        yield GeojsonPointItem(**properties)

    def parse(self, response):
        urls = response.xpath('//div[@class="brand_list_viewer"]/div[@class="column"]/ul/li/a/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)
