import re
from typing import Any, Iterable
from urllib.parse import urlsplit

from scrapy import Spider
from scrapy.http import Response

from locations.categories import apply_category
from locations.items import Feature


class KoerperformenSpider(Spider):
    name = "koerperformen"
    item_attributes = {"brand": "Körperformen", "brand_wikidata": "Q117455940"}
    start_urls = ["https://www.körperformen.com/studiosuche/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        re_address = re.compile(r"(.*) I (.*?) (.*)")
        for shop in response.xpath('//div[@class="studios-suche-wrapper"]//div[@class="studio-row"]'):
            addr_raw = ", ".join(
                addr for addr in map(str.strip, shop.xpath('div[@class="studio-row-con"]/text()').getall()) if addr
            )
            street, postcode, city = re_address.match(addr_raw).groups()
            website = shop.xpath("a/@href").get()
            host = urlsplit(website).netloc
            item = Feature(
                {
                    "ref": website.split("/")[-2],
                    "branch": shop.xpath("descendant::h3/text()").get().removeprefix("Körperformen").strip(),
                    "street_address": street,
                    "postcode": postcode,
                    "city": city,
                    "website": website.replace(host, host.encode().decode("idna")),
                    "lat": shop.xpath('span[@class="studio-koordination"]/text()').get(),
                    "lon": shop.xpath('span[@class="studio-koordinaten_longitude"]/text()').get(),
                }
            )
            apply_category({"leisure": "fitness_centre"}, item)
            yield item
