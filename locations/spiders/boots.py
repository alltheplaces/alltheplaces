import scrapy

from locations.items import GeojsonPointItem


class BootsSpider(scrapy.Spider):
    name = "boots"
    item_attributes = {"brand": "Boots", "brand_wikidata": "Q6123139"}
    allowed_domains = ["www.boots.com", "www.boots.ie"]
    download_delay = 0.5
    start_urls = ["http://www.boots.com/store-a-z", "http://www.boots.ie/store-a-z"]

    def parse_hours(self, lis):
        hours = []
        for li in lis:
            day = li.xpath(
                'normalize-space(./td[@class="store_hours_day"]/text())'
            ).extract_first()
            times = (
                li.xpath('normalize-space(./td[@class="store_hours_time"]/text())')
                .extract_first()
                .replace(" ", "")
                .replace("Closed-Closed", "off")
            )
            if times and day:
                hours.append(day[:2] + " " + times)

        return "; ".join(hours)

    def parse_stores(self, response):
        addr_full = response.xpath(
            '//section[@class="store_details_content rowContainer"]/dl[@class="store_info_list"][1]/dd[@class="store_info_list_item"]/text()'
        ).extract()
        address = ", ".join(map(str.strip, addr_full))
        # Handle blank store pages e.g. https://www.boots.com/stores/2250-alnwick-paikes-street-ne66-1hx
        if len(address) == 0:
            return

        properties = {
            "ref": response.xpath(
                'normalize-space(//input[@id="bootsStoreId"]/@value)'
            ).extract_first(),
            "name": response.xpath(
                'normalize-space(//input[@id="inputLocation"][@name="inputLocation"]/@value)'
            ).extract_first(),
            "postcode": response.xpath(
                'normalize-space(//input[@id="storePostcode"]/@value)'
            ).extract_first(),
            "addr_full": address,
            "phone": response.xpath(
                '//section[@class="store_details_content rowContainer"]/dl[@class="store_info_list"][3]/dd[@class="store_info_list_item"]/a/text()'
            ).extract_first(),
            "country": response.xpath(
                'normalize-space(//input[@id="countryCode"][@name="countryCode"]/@value)'
            ).extract_first(),
            "website": response.url,
            "lat": response.xpath(
                'normalize-space(//input[@id="lat"]/@value)'
            ).extract_first(),
            "lon": response.xpath(
                'normalize-space(//input[@id="lon"]/@value)'
            ).extract_first(),
        }

        hours = self.parse_hours(
            response.xpath(
                '//div[@class="row store_all_opening_hours"]/div[1]/table[@class="store_opening_hours "]/tbody/tr'
            )
        )
        if hours:
            properties["opening_hours"] = hours

        if properties["name"].startswith("Opticians - "):
            properties["brand"] = "Boots Opticians"
            properties["brand_wikidata"] = "Q4944037"
            properties["name"] = properties["name"][12:]

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        urls = response.xpath(
            '//div[@class="brand_list_viewer"]/div[@class="column"]/ul/li/a/@href'
        ).extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)
