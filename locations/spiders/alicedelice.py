import scrapy

from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class AliceDeliceSpider(scrapy.Spider):
    name = "alicedelice"
    item_attributes = {"brand": "Alice Délice", "brand_wikidata": "Q105099543"}
    allowed_domains = ["www.alicedelice.com"]
    start_urls = ("https://www.alicedelice.com/trouver-ma-boutique",)

    def parse(self, response):
        response.selector.remove_namespaces()
        links = response.xpath("//div[@class='store-select']/select/option/a/@href").getall()
        links = [response.urljoin(link) for link in links]
        for link in links:
            yield scrapy.Request(link, callback=self.parse_store)

    def parse_store(self, response):
        store_name = response.xpath("//store/@name").get()

        street_address_parts = response.xpath(
            "//h1/following-sibling::*/span[@class='city']/preceding-sibling::*/text()"
        ).getall()
        street_address = clean_address(street_address_parts)

        city_raw = response.xpath("//h1/following-sibling::*/span[@class='city']/span[3]/text()").get()
        city = city_raw.strip() if city_raw is not None else None

        postcode_raw = response.xpath("//h1/following-sibling::*/span[@class='city']/span[2]/text()").get()
        postcode = postcode_raw.strip() if postcode_raw is not None else None

        phone_raw = response.xpath(
            "//h1/following-sibling::*/span[@class='city']" "/following-sibling::a[contains(@href,'tel')]/strong/text()"
        ).get()
        phone = phone_raw.strip().replace(".", "").replace("-", "") if phone_raw is not None else None

        facebook_full_url = response.xpath(
            "//h1/following-sibling::*/span[@class='city']" "/following-sibling::a[contains(@href,'facebook')]/@href"
        ).get()
        facebook = facebook_full_url.split("/")[3] if facebook_full_url is not None else None

        lat = response.xpath("//store/@latitude").get()
        lon = response.xpath("//store/@longitude").get()
        geo = dict(lat=lat, lon=lon)

        if float(lat) == 0.0 or float(lon) == 0.0:
            geo = {}

        properties = dict(
            name=store_name,
            website=response.url,
            street_address=street_address,
            city=city,
            postcode=postcode,
            phone=phone,
            facebook=facebook,
            ref=response.url.split("/")[-1],
            country="FR",
            **geo,
        )

        yield Feature(**properties)
