import scrapy
import re
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class LoftSpider(scrapy.Spider):
    name = "loft"
    item_attributes = {"brand": "Loft", "brand_wikidata": "Q62075137"}
    allowed_domains = ["stores.loft.com"]
    download_delay = 0
    start_urls = (
        "https://stores.loft.com/",
        "https://stores.loft.com/outlet/index.html",
    )

    country_url_pattern = re.compile(r"^(..\/|..\/outlet\/)[a-z]{2}.html$")
    state_url_pattern = re.compile(r"^(..\/|..\/outlet\/|)[a-z]{2}\/[^(\/)]+.html$")
    city_url_pattern = re.compile(
        r"^(..\/|)([a-z]{2}|outlet)\/[a-z]{2}\/[^(\/)]+.html$"
    )
    store_url_pattern = re.compile(
        r"^(..\/|..\/outlet\/)?[a-z]{2}\/[^(\/)]+\/[^(\/)]+\/[^(\/)]+.html$"
    )

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        for hour in hours:
            day, hrs = hour.split(" ")
            if hrs == "Closed":
                continue
            open_time, close_time = hrs.split("-")
            opening_hours.add_range(
                day=day, open_time=open_time, close_time=close_time, time_format="%H:%M"
            )

        return opening_hours.as_opening_hours()

    def parse_stores(self, response):
        brand = response.xpath(
            'normalize-space(//h1[@itemprop="name"]/text())'
        ).extract_first()
        if "closed" in brand.lower():
            return
        properties = {
            "name": response.xpath('//h1[@itemprop="name"]/div/text()').extract_first(),
            "addr_full": response.xpath(
                'normalize-space(//span[@itemprop="streetAddress"]/text())'
            ).extract_first(),
            "phone": response.xpath(
                'normalize-space(//span[@itemprop="telephone"]/text())'
            ).extract_first(),
            "city": response.xpath(
                'normalize-space(//span[@itemprop="addressLocality"]/text())'
            )
            .extract_first()
            .strip(","),
            "state": response.xpath(
                'normalize-space(//span[@itemprop="addressRegion"]/text())'
            ).extract_first(),
            "postcode": response.xpath(
                'normalize-space(//span[@itemprop="postalCode"]/text())'
            ).extract_first(),
            "country": response.xpath(
                'normalize-space(//abbr[@itemprop="addressCountry"]/text())'
            ).extract_first(),
            "ref": "_".join(
                re.search(r".+/(.+?)/(.+?)/(.+?)/?(?:\.html|$)", response.url).groups()
            ),
            "website": response.url,
            "lat": response.xpath(
                'normalize-space(//meta[@itemprop="latitude"]/@content)'
            ).extract_first(),
            "lon": response.xpath(
                'normalize-space(//meta[@itemprop="longitude"]/@content)'
            ).extract_first(),
            "brand": brand,
        }

        opening_hours = self.parse_hours(
            response.xpath('//tr[@itemprop="openingHours"]/@content').extract()
        )
        if opening_hours:
            properties["opening_hours"] = opening_hours

        yield GeojsonPointItem(**properties)

    def parse_city_stores(self, response):
        stores = response.xpath('//a[text()="Visit Store Page"]/@href').extract()
        for store in stores:
            yield scrapy.Request(response.urljoin(store), callback=self.parse_stores)

    def parse_state(self, response):
        urls = response.xpath(
            '//div[@class="c-directory-list-content-wrapper"]/ul/li/a/@href'
        ).extract()
        for path in urls:
            if self.store_url_pattern.match(path.strip()):
                yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)
            else:
                yield scrapy.Request(
                    response.urljoin(path), callback=self.parse_city_stores
                )

    def parse_country(self, response):
        urls = response.xpath(
            '//div[@class="c-directory-list-content-wrapper"]/ul/li/a/@href'
        ).extract()

        for path in urls:
            if self.store_url_pattern.match(path.strip()):
                yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)
            elif self.city_url_pattern.match(path.strip()):
                yield scrapy.Request(
                    response.urljoin(path), callback=self.parse_city_stores
                )
            else:
                yield scrapy.Request(response.urljoin(path), callback=self.parse_state)

    def parse(self, response):
        urls = response.xpath(
            '//div[@class="c-directory-list-content-wrapper"]/ul/li/a/@href'
        ).extract()
        for path in urls:
            if self.store_url_pattern.match(path.strip()):
                yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)
            elif self.city_url_pattern.match(path.strip()):
                yield scrapy.Request(
                    response.urljoin(path), callback=self.parse_city_stores
                )
            elif self.state_url_pattern.match(path.strip()):
                yield scrapy.Request(response.urljoin(path), callback=self.parse_state)
            else:
                yield scrapy.Request(
                    response.urljoin(path), callback=self.parse_country
                )
