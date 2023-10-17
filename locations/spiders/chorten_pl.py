from scrapy import Request, Spider
from scrapy.http import Response

from locations.hours import DAYS_PL, OpeningHours
from locations.items import Feature


class ChortenPLSpider(Spider):
    name = "chorten_pl"
    item_attributes = {"brand": "Chorten", "brand_wikidata": "Q48843988"}
    start_urls = ["https://chorten.com.pl/sklepy/lista/"]

    def parse(self, response: Response, **kwargs):
        for store_url in response.xpath("//a[@class='s_link']/@href").getall():
            yield Request(url=store_url, callback=self.parse_store)

        if response.url == self.start_urls[0]:
            last_page_number = max(
                map(
                    lambda x: int(x.removeprefix("https://chorten.com.pl/sklepy/lista/p").removesuffix("?")),
                    response.xpath("//a[@class='page-link']/@href").getall(),
                )
            )
            for i in range(2, last_page_number + 1):
                yield Request(url=f"https://chorten.com.pl/sklepy/lista/p{i}?")

    def parse_store(self, response: Response, **kwargs):
        address_lines = list(map(str.strip, response.xpath("//address/text()").getall()))
        opening_hours = OpeningHours()
        days_and_hours = list(
            filter(
                lambda h: len(h) > 0,
                map(str.strip, response.xpath("//dl[contains(@class, 'godziny')]/*/text()").getall()),
            )
        )
        for day, hours in zip(days_and_hours[0::2], days_and_hours[1::2]):
            opening_hours.add_ranges_from_string(f"{day} {hours}", days=DAYS_PL)
        properties = {
            "lat": response.xpath("//div[@id='sklep-mapa']/@data-lat").get(),
            "lon": response.xpath("//div[@id='sklep-mapa']/@data-lng").get(),
            "street_address": address_lines[0],
            "postcode": address_lines[1].split(" ")[0],
            "city": " ".join(address_lines[1].split(" ")[1:]),
            "opening_hours": opening_hours,
            "website": response.url,
            "ref": response.url.split("_")[-1],
        }
        yield Feature(**properties)
