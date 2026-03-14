import re
from typing import AsyncIterator, Iterable
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import FormRequest, Request, Response

from locations.categories import Categories, apply_category
from locations.geo import country_iseadgg_centroids
from locations.hours import CLOSED_DE, DAYS_DE, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class VolgCHSpider(Spider):
    name = "volg_ch"
    item_attributes = {"brand": "Volg", "brand_wikidata": "Q2530746"}
    allowed_domains = ["www.volg.ch"]
    start_urls = [
        "https://www.volg.ch/standorte-oeffnungszeiten/?tx_kochvolgstores_storelist[action]=search&tx_kochvolgstores_storelist[controller]=Stores"
    ]

    async def start(self) -> AsyncIterator[FormRequest]:
        for lat, lon in country_iseadgg_centroids(["CH", "LI"], 24):
            yield FormRequest(
                url=self.start_urls[0],
                callback=self.parse_store_list,
                formdata={
                    "tx_kochvolgstores_storelist[latitude]": str(lat),
                    "tx_kochvolgstores_storelist[longitude]": str(lon),
                    "tx_kochvolgstores_storelist[location]": "",
                },
            )

    def parse_store_list(self, response: Response) -> Iterable[Request]:
        for store_slug in list(
            map(
                lambda x: x.split("?", 1)[0],
                response.xpath('//div[contains(@class, "c-location-list__link")]/a/@href').getall(),
            )
        ):
            yield Request(
                url=urljoin("https://{}".format(self.allowed_domains[0]), store_slug), callback=self.parse_store
            )

    def parse_store(self, response: Response) -> Iterable[Feature]:
        properties = {
            "ref": response.xpath('//link[@rel="canonical"]/@href').get().split("/volg-", 1)[1].split("/", 1)[0],
            "branch": response.xpath('//div[contains(@class, "c-content__header")]//h1/text()')
            .get()
            .removeprefix("Volg "),
            "lat": response.xpath("//@data-lat").get(),
            "lon": response.xpath("//@data-lng").get(),
            "addr_full": merge_address_lines(
                response.xpath(
                    '//div[contains(@class, "c-content__main")]/section[2]/div[contains(@class, "container")]/div[1]/div[2]/div[1]/div[1]/p[1]/text()'
                ).getall()
            ),
            "phone": response.xpath(
                '//div[contains(@class, "c-content__main")]/section[2]/div[contains(@class, "container")]/div[1]/div[2]/div[1]/div[1]/p[2]/a/@href'
            )
            .get()
            .removeprefix("tel:"),
            "website": response.url,
            "opening_hours": OpeningHours(),
        }
        hours_string = re.sub(
            r"\s+",
            " ",
            " ".join(
                response.xpath(
                    '//table[contains(@class, "c-location-hours")]//td[position() = 1 or position() = 3]/text()'
                ).getall()
            ),
        )
        properties["opening_hours"].add_ranges_from_string(hours_string, days=DAYS_DE, closed=CLOSED_DE)
        apply_category(Categories.SHOP_SUPERMARKET, properties)
        properties["extras"].update(self.parse_extras(response))
        yield Feature(**properties)

    @staticmethod
    def parse_extras(response: Response) -> dict:
        extras = {}
        services = list(map(str.strip, response.xpath('//ul[contains(@class, "c-location-offer")]//text()').getall()))
        if "Postagentur" in services:
            extras.update(
                {
                    "post_office": "post_partner",
                    "post_office:brand": "Die Post",
                    "post_office:brand:wikidata": "Q614803",
                }
            )
        if "Heimlieferservice" in services:
            extras.update(
                {
                    "delivery": "yes",
                    "delivery:partner": "Die Post",
                    "delivery:partner:wikidata": "Q614803",
                }
            )
        return extras
