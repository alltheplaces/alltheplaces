from typing import Any
from urllib.parse import urljoin

from scrapy import Request
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.items import Feature
from locations.user_agents import CHROME_LATEST


class MetroCashAndCarrySpider(SitemapSpider):
    name = "metro_cash_and_carry"
    user_agent = CHROME_LATEST
    requires_proxy = True
    sitemap_rules = [
        # A better way to get all shop URLs was not found.
        ("/metro-maerkte/", "parse"),  # at
        ("/magazini/", "parse"),  # bg
        ("/veleprodajni-centri/", "parse"),  # hr
        ("/prodejny/", "parse"),  # cz
        ("/halles/", "parse"),  # fr
        ("/standorte/", "parse"),  # de
        ("/aruhazak/", "parse"),  # hu
        ("/punti-vendita/", "parse"),  # it
        ("/magaziny/", "parse"),  # kz
        ("/magazine/", "parse"),  # md
        ("/vestigingen/", "parse"),  # nl
        ("/store-locator/", "parse"),  # pk, ua
        ("/hale/", "parse"),  # pl
        ("/lojas/", "parse"),  # pt
        ("/magazinele-noastre/", "parse"),  # ro
        ("/torgovye-centry/", "parse"),  # ru
        ("/distributivni-centri/", "parse"),  # rs
        ("/predajne/", "parse"),  # sk
        ("/tiendas/", "parse"),  # es
        ("/magazalar/", "parse"),  # tr
    ]
    METRO = ("Metro", "Q13610282")
    MAKRO = ("Makro", "Q704606")

    def start_requests(self):
        yield Request(
            "https://www.metroag.de/en/about-us/brands",
            callback=self.get_sitemaps,
        )

    def get_sitemaps(self, response: Response):
        country_urls = response.xpath("//div[@id='metro-and-makro']//a[@href and not(@class)]/@href").getall()
        for url in country_urls:
            if url.startswith("http"):
                yield Request(urljoin(url, "sitemap.xml"), callback=self._parse_sitemap)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # Parse only store pages and ignore everything else (e.g. city-specific page https://www.metro.de/standorte/hannover)
        if response.xpath("//div[@data-store-id]"):
            item = Feature()
            item["ref"] = response.url
            item["branch"] = response.xpath("//h1[contains(@class, 'h1 store-name')]/text()").get(default="").strip()
            item["addr_full"] = "".join(
                response.xpath("//a[contains(@class, 'store-address')]/text()").getall()
            ).strip()
            coords = url_to_coords(response.xpath("//a[contains(@class, 'store-address')]/@href").get(default=""))
            if coords:
                item["lat"], item["lon"] = coords
            item["phone"] = response.xpath("//a[contains(@class, 'store-phone')]/@href").get()
            item["email"] = (
                response.xpath("//a[contains(@class, 'store-email')]/@href").get(default="").removeprefix("mailto:")
            )
            item["website"] = response.url

            if "makro" in response.url:
                item["brand"], item["brand_wikidata"] = self.MAKRO
            else:
                item["brand"], item["brand_wikidata"] = self.METRO
            apply_category(Categories.SHOP_WHOLESALE, item)
            # TODO: opening_hours (days format differs per country)
            yield item
