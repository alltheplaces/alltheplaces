# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem


class ShopkoSpider(scrapy.Spider):
    name = "shopko"
    item_attributes = {"brand": "Shopko"}
    allowed_domains = ["shopko.com"]
    start_urls = ("http://www.shopko.com/sitemaps_list.jsp?seq_no=1&typeName=store",)

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath("//url/loc/text()").extract()
        for path in city_urls:
            locationURL = re.compile(
                r"http:/(/|/www.)shopko.com/\S+/store_details\S+=\d+"
            )
            if not re.search(locationURL, path):
                pass
            else:
                yield scrapy.Request(
                    path.strip(),
                    callback=self.parse_store,
                )

    def parse_store(self, response):

        properties = {
            "name": response.xpath("/html/body/div[1]/div[2]/div/div[2]/div[2]/h1")
            .extract()[0]
            .split("</i>")[1]
            .strip("</h1>"),
            "website": response.request.url,
            "ref": response.xpath("/html/body/div[1]/div[2]/div/div[2]/div[2]/h1")
            .extract()[0]
            .split("</i>")[1]
            .strip("</h1>"),
            "addr_full": " ".join(
                response.xpath(
                    "/html/body/div[1]/div[2]/div/div[2]/div[2]/div[1]/text()"
                )
                .extract()[0]
                .split()
            ),
            "city": " ".join(
                response.xpath(
                    "/html/body/div[1]/div[2]/div/div[2]/div[2]/div[1]/text()"
                )
                .extract()[1]
                .split()
            ).split(",")[0],
            "state": " ".join(
                response.xpath(
                    "/html/body/div[1]/div[2]/div/div[2]/div[2]/div[1]/text()"
                )
                .extract()[1]
                .split()
            )
            .split(",")[1]
            .split()[0],
            "postcode": " ".join(
                response.xpath(
                    "/html/body/div[1]/div[2]/div/div[2]/div[2]/div[1]/text()"
                )
                .extract()[1]
                .split()
            )
            .split(",")[1]
            .split()[1],
            "opening_hours": str(
                " ".join(
                    response.xpath(
                        "/html/body/div[1]/div[2]/div/div[2]/div[2]/div[4]/text()"
                    ).extract()
                ).split()
            )
            .replace(",", "")
            .replace("[", "")
            .replace("'", ""),
            "lon": float(
                response.xpath("/html/body/div[1]/div[2]/div/script[3]/text()")
                .extract()[0]
                .split("store.lng = ")[1]
                .split(";")[0]
            ),
            "lat": float(
                response.xpath("/html/body/div[1]/div[2]/div/script[3]/text()")
                .extract()[0]
                .split("store.lat = ")[1]
                .split(";")[0]
            ),
        }

        yield GeojsonPointItem(**properties)
