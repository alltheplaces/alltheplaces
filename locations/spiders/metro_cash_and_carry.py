import re
from typing import Any
from urllib.parse import urljoin

from scrapy import Request, Selector
from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.user_agents import BROWSER_DEFAULT


class MetroCashAndCarrySpider(Spider):
    name = "metro_cash_and_carry"
    METRO = ("Metro", "Q13610282")
    MAKRO = ("Makro", "Q704606")
    start_urls = ["https://cdn.metro-online.com/bundles/js-store-locator.js"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": BROWSER_DEFAULT,
        "CONCURRENT_REQUESTS": 1,
        "DOWNLOAD_TIMEOUT": 120,
    }
    # API query params default values
    s = "0F3B38A3-7330-4544-B95B-81FC80A6BB6F"
    v = "D5BC0757-6F6D-4BDB-BFBD-065D34D0B4A3"
    requires_proxy = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # Check for updated values
        if match := re.search(r"s={([A-Fa-f0-9-]+)}&v={([A-Fa-f0-9-]+)}", response.text):
            self.s, self.v = match.groups()
        yield Request(url="https://www.metroag.de/en/about-us/brands", callback=self.parse_country)

    def parse_country(self, response: Response, **kwargs: Any) -> Any:
        for url in response.xpath('//a[contains(@title, "MAKRO") or contains(@title, "METRO")]/@href').getall():
            if re.search(r"www\.(metro|makro)[-.]", url):
                yield JsonRequest(
                    urljoin(
                        url,
                        f"/sxa/search/results?s={self.s}&v={self.v}&p=1000&o=StoreName,Ascending&g=",
                    ),
                    callback=self.parse_locations,
                )

    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json().get("Results", []):
            html = Selector(text=location.get("Html", ""))
            item = Feature()
            item["ref"] = location["Id"]
            item["lat"] = location["Geospatial"]["Latitude"]
            item["lon"] = location["Geospatial"]["Longitude"]
            if "makro" in response.url:
                item["brand"], item["brand_wikidata"] = self.MAKRO
            else:
                item["brand"], item["brand_wikidata"] = self.METRO
            item["name"] = item["brand"]
            item["branch"] = (
                html.xpath("//*[contains(@class, 'poi-store-name')]/text()")
                .get("")
                .strip()
                .removeprefix(f'{item["brand"].upper()} ')
            )
            item["addr_full"] = clean_address(html.xpath("//a[contains(@href, 'maps')]/text()").getall())
            item["phone"] = html.xpath("//a[contains(@href, 'tel:')]/@href").get()
            item["email"] = html.xpath("//a[contains(@href, 'mailto:')]/@href").get()
            item["website"] = response.urljoin(html.xpath('//a[contains(@class, "store-info-button")]/@href').get(""))

            apply_category(Categories.SHOP_WHOLESALE, item)
            # TODO: opening_hours (days format differs per country)
            yield item
