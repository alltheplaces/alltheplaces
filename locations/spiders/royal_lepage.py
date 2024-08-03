import re

import scrapy

from locations.items import Feature


class RoyalLepageSpider(scrapy.Spider):
    name = "royal_lepage"
    item_attributes = {"brand": "Royal LePage", "brand_wikidata": "Q7374385"}
    allowed_domains = ["royallepage.ca"]
    start_urls = [
        "https://www.royallepage.ca/en/search/offices/?lat=&lng=&address=&designations=&address_type=&city_name=&prov_code=&sortby=&transactionType=OFFICE&name=&location=&language=&specialization=All"
    ]

    def parse_location(self, response):
        map_script = response.xpath('//script/text()[contains(., "staticMap")]').get()
        lat = re.search("latitude: (.*?),?$", map_script, flags=re.M).group(1)
        lon = re.search("longitude: (.*?),?$", map_script, flags=re.M).group(1)

        properties = {
            "brand": "Royal LePage",
            "ref": re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1),
            "name": response.xpath('normalize-space(//*[@itemprop="name"]//text())').extract_first().strip(" *"),
            "addr_full": response.xpath('normalize-space(//*[@itemprop="address"]/p/text())').extract_first(),
            "country": "CA",
            "phone": response.xpath('normalize-space(//a[@itemprop="telephone"]//text())').extract_first(),
            "website": response.url,
            "lat": float(lat) if lat else None,
            "lon": float(lon) if lon else None,
        }

        yield Feature(**properties)

    def parse(self, response):
        urls = response.xpath("//address//a/@href").extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_location)

        next_page = response.xpath(
            '//div[contains(@class, "paginator")]//li[@class="is-active"]/following-sibling::li//a/@href'
        ).extract_first()
        if next_page:
            yield scrapy.Request(response.urljoin(next_page))
