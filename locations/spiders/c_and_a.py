import json
import re

import scrapy

from locations.items import Feature


class CAndASpider(scrapy.Spider):
    name = "c_and_a"
    item_attributes = {"brand": "C&A", "brand_wikidata": "Q701338"}
    allowed_domains = ["www.c-and-a.com"]
    start_urls = (
        "https://www.c-and-a.com/stores/nl-nl/index.html",
        "https://www.c-and-a.com/stores/de-de/index.html",
        "https://www.c-and-a.com/stores/be-nl/index.html",
        "https://www.c-and-a.com/stores/fr-fr/index.html",
        "https://www.c-and-a.com/stores/es-es/index.html",
        "https://www.c-and-a.com/stores/ch-de/index.html",
        "https://www.c-and-a.com/stores/lu-fr/index.html",
        "https://www.c-and-a.com/stores/at-de/index.html",
        "https://www.c-and-a.com/stores/pt-pt/index.html",
        "https://www.c-and-a.com/stores/cz-cz/index.html",
        "https://www.c-and-a.com/stores/pl-pl/index.html",
        "https://www.c-and-a.com/stores/hu-hu/index.html",
        "https://www.c-and-a.com/stores/sk-sk/index.html",
        "https://www.c-and-a.com/stores/si-si/index.html",
        "https://www.c-and-a.com/stores/it-it/index.html",
        "https://www.c-and-a.com/stores/ro-ro/index.html",
        "https://www.c-and-a.com/stores/hr-hr/index.html",
        "https://www.c-and-a.com/stores/rs-rs/index.html",
    )

    postcode_pattern = r"^(\d+[- ]?(?:\d+|[A-Z]{2})) (.*)$"

    def parse(self, response):
        pages = response.xpath(
            '//div[@class="overviewCities"]/div/div/a[contains(concat(" ", normalize-space(@class), " "), " allcities ")]/@href'
        ).extract()
        for page in pages:
            yield scrapy.Request(response.urljoin(page), callback=self.parse_city)

    def parse_city(self, response):
        stores = response.xpath(
            '//section[@class="resultFilter"]/div/div/div[contains(concat(" ", normalize-space(@class), " "), " store ")]'
        )
        country = find_between(response.url, "stores/", "-").upper()
        for store in stores:
            flags = json.loads(store.xpath("./@data-flags").get())
            contact = [i.strip() for i in store.xpath('./div[@class="addressBox"]/p[@class="Kontakt"]/text()').getall()]
            address = [i.strip() for i in store.xpath('./div[@class="addressBox"]/p[@class="address"]/text()').getall()]
            hours = [
                i.xpath("./@data-day").get()[0:2]
                + " "
                + i.xpath("./@data-openingtime").get()
                + "-"
                + i.xpath("./@data-closingtime").get()
                for i in store.xpath('./div[@class="addressBox"]/p[@class="openingHours hideopeninghours"]')
            ]

            try:
                postcode, city = re.findall(self.postcode_pattern, address[1])[0]
            except:
                postcode, city = None, address[1]

            properties = {
                "ref": store.xpath("./@id").get(),
                "website": response.urljoin(
                    store.xpath(
                        './div[@class="addressBox"]/p[@class="addBoxLinks"]/a[@class="btn cabtnBigRed"]/@href'
                    ).get()
                ),
                "name": store.xpath('./div[@class="addressBox"]/p[@class="store"]/text()').get(),
                "phone": contact[2].replace("Tel: ", ""),
                "country": country,
                "opening_hours": "; ".join(hours),
                "street_address": address[0],
                "postcode": postcode,
                "city": city,
                "addr_full": ", ".join(address),
                "extras": {
                    "wheelchair": "yes" if "wheelchairflag" in flags else "no",
                    # "email": contact[1].replace("Tel: ", ""),
                },
            }

            properties["image"] = "https://www.c-and-a.com/shop-img/ca-store/" + properties["ref"] + ".JPG"

            link = (
                store.xpath('./div[@class="addressBox"]/p[@class="addBoxLinks"]/a[@class="filLink"]/@href')
                .get()
                .split("/")
            )
            if len(link) > 6:
                if link[6][0:1] == "@":
                    coords = link[6][1:].split(",")

                    properties["lat"] = coords[0]
                    properties["lon"] = coords[1]

            yield Feature(**properties)


def find_between(s, first, last):
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return s[start:end]
    except ValueError:
        return ""
