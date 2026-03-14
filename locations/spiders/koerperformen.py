import re

from scrapy import Spider

from locations.items import Feature


class KoerperformenSpider(Spider):
    name = "koerperformen"
    item_attributes = {"brand": "Körperformen", "brand_wikidata": "Q117455940"}
    start_urls = ["https://www.körperformen.com/studiosuche/"]

    def parse(self, response, **kwargs):
        re_address = re.compile(r"(.*) I (.*?) (.*)")
        for shop in response.xpath('//div[@class="studio-row"]'):
            addr_raw = ", ".join(
                addr for addr in map(str.strip, shop.xpath('div[@class="studio-row-con"]/text()').getall()) if addr
            )
            street, postcode, city = re_address.match(addr_raw).groups()
            website = shop.xpath("a/@href").get()
            yield Feature(
                {
                    "ref": website.split("/")[-2],
                    "name": shop.xpath("descendant::h3/text()").get(),
                    "street_address": street,
                    "postcode": postcode,
                    "city": city,
                    "website": website,
                    "lat": float(shop.xpath('span[@class="studio-koordination"]/text()').get()),
                    "lon": float(shop.xpath('span[@class="studio-koordinaten_longitude"]/text()').get()),
                }
            )
