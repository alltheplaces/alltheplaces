import re
from typing import Iterable

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories
from locations.hours import DAYS_ES, DELIMITERS_ES, OpeningHours
from locations.items import Feature


class DinosolESSpider(Spider):
    name = "dinosol_es"
    allowed_domains = ["www.hiperdino.es"]
    start_urls = ["https://www.hiperdino.es/c9504/tiendas/"]
    brands = [
        (
            "HIPERDINO EXPRESS",
            {"brand": "HiperDino Express", "brand_wikidata": "Q105955317", "extras": Categories.SHOP_CONVENIENCE.value},
        ),
        (
            "HiperDino Express",
            {"brand": "HiperDino Express", "brand_wikidata": "Q105955317", "extras": Categories.SHOP_CONVENIENCE.value},
        ),
        (
            "HIPERDINO",
            {"brand": "HiperDino", "brand_wikidata": "Q105955292", "extras": Categories.SHOP_SUPERMARKET.value},
        ),
        (
            "HiperDino",
            {"brand": "HiperDino", "brand_wikidata": "Q105955292", "extras": Categories.SHOP_SUPERMARKET.value},
        ),
        (
            "SUPERDINO",
            {"brand": "SuperDino", "brand_wikidata": "Q105955304", "extras": Categories.SHOP_SUPERMARKET.value},
        ),
        (
            "SuperDino",
            {"brand": "SuperDino", "brand_wikidata": "Q105955304", "extras": Categories.SHOP_SUPERMARKET.value},
        ),
    ]
    download_delay = 0.2

    def parse(self, response: Response):
        for island_id in response.xpath('//select[@name="island"]/option/@value').getall():
            yield from self.request_page(island_id, 1)

    def request_page(self, island_id: int, page_number: int) -> Iterable[Request]:
        yield Request(
            url=f"https://www.hiperdino.es/c9504/tiendas/index/result/?island={island_id}&p={page_number}",
            callback=self.parse_stores_list,
            meta={"island_id": island_id, "page_number": page_number},
        )

    def parse_stores_list(self, response: Response):
        # Parse individual store pages
        store_pages = response.xpath('//div[contains(@class, "tiendas__info")]/span/a/@href').getall()
        for store_page in store_pages:
            yield Request(url=store_page, callback=self.parse_store)

        # Parse all other pages of store locations for each island
        current_page_number = response.meta["page_number"]
        if current_page_number == 1:
            island_id = response.meta["island_id"]
            total_pages = int(
                response.xpath('//div[contains(@class, "table-container--pagination__numeration")]//span[2]/text()')
                .get()
                .strip()
            )
            for page_number in range(2, total_pages, 1):
                yield from self.request_page(island_id, page_number)

    def parse_store(self, response: Response):
        properties = {
            "ref": response.xpath('//div[contains(@class, "tienda__item")]/@data-store').get(),
            "name": response.xpath('//div[contains(@class, "detail_store")]/@data-store').get(),
            "lat": response.xpath('//div[contains(@class, "tienda__item")]/@data-lat').get(),
            "lon": response.xpath('//div[contains(@class, "tienda__item")]/@data-lon').get(),
            "addr_full": re.sub(
                r"\s+", " ", " ".join(response.xpath('//div[contains(@class, "tienda__item")]/p[1]/text()').getall())
            ).strip(),
            "phone": re.sub(
                r"\s+", " ", " ".join(response.xpath('//div[contains(@class, "tienda__item")]/p[3]/text()').getall())
            )
            .split("/", 1)[0]
            .strip(),
            "opening_hours": OpeningHours(),
            "website": response.url,
        }
        if not properties["name"]:
            properties["name"] = (
                response.xpath('//div[@class="page-corporate__tiendas"]/div[1]/div[1]/div[1]/h3/text()').get().strip()
            )

        # Ignore warehouses
        if properties["name"].upper().startswith("CENTRO DISTRIBUCIÓN ONLINE"):
            return

        # Brand detection
        if properties["name"]:
            for brand in self.brands:
                if properties["name"].startswith(brand[0]):
                    properties |= brand[1]
                    properties["name"] = properties["name"].removeprefix(brand[0]).strip()
                    break
        else:
            self.logger.error("Name could not be determined from store webpage: {}".format(response.url))
        if not properties.get("brand"):
            self.logger.error("Brand could not be determined from store webpage: {}".format(response.url))

        # Opening hours
        hours_string = re.sub(
            r"\s+", " ", " ".join(response.xpath('//div[contains(@class, "tienda__item")]/p[2]/text()').getall())
        ).strip()
        properties["opening_hours"].add_ranges_from_string(hours_string, days=DAYS_ES, delimiters=DELIMITERS_ES)

        yield Feature(**properties)
