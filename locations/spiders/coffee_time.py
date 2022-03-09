import scrapy
from locations.items import GeojsonPointItem


class BobsSpider(scrapy.Spider):
    name = "coffeetime"
    item_attributes = {"brand": "Coffee Time"}
    allowed_domains = ["www.coffeetime.com"]
    start_urls = [
        "http://www.coffeetime.com/locations.aspx?address=&Countryui=CA&pageNumber=1"
    ]

    def parse_store(self, response):
        container = response.xpath('//div[contains(@class, "col-md-9")]')
        for i in container:
            street = i.xpath(".//div/p[1]/text()").extract_first().strip()
            cty_st_zip = i.xpath(".//div/p[2]/text()").extract_first().strip()

            # Keep missing phone/<li> from breaking script
            if i.xpath(".//div/ul/li[2]/p/text()").extract_first():
                phone = i.xpath(".//div/ul/li[1]/p/text()").extract_first().strip()
            else:
                phone = ""

            if i.xpath(".//div/ul/li[2]/p/a/@href").extract_first():
                lat = (
                    i.xpath(".//div/ul/li[2]/p/a/@href")
                    .extract_first()
                    .split("=")[2]
                    .split(",")[0]
                )
                lon = (
                    i.xpath(".//div/ul/li[2]/p/a/@href")
                    .extract_first()
                    .split("=")[2]
                    .split(",")[1]
                )
            else:
                lat = (
                    i.xpath(".//div/ul/li/p/a/@href")
                    .extract_first()
                    .split("=")[2]
                    .split(",")[0]
                )
                lon = (
                    i.xpath(".//div/ul/li/p/a/@href")
                    .extract_first()
                    .split("=")[2]
                    .split(",")[1]
                )

            city = cty_st_zip.split(", ")[0]
            state = cty_st_zip.split(", ")[1].split(", ")[0]
            postcode = cty_st_zip.split(", ")[2]

            addr_full = "{} {}, {} {}".format(street, city, state, postcode)

            yield GeojsonPointItem(
                ref=street,
                city=city,
                state=state,
                postcode=postcode,
                addr_full=addr_full,
                phone=phone,
                lat=float(lat),
                lon=float(lon),
                country="CA",
            )

    def parse(self, response):
        base_url = (
            "http://www.coffeetime.com/locations.aspx?"
            "address=&Countryui=CA&pageNumber="
        )
        for i in range(1, 9):
            page = base_url + str(i)
            yield scrapy.Request(page, callback=self.parse_store)
