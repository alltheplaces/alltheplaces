import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.user_agents import BROWSER_DEFAULT


class DominosPizzaDESpider(SitemapSpider):
    name = "dominos_pizza_de"
    item_attributes = {"brand": "Domino's", "brand_wikidata": "Q839466"}
    allowed_domains = ["dominos.de"]
    sitemap_urls = ["https://www.dominos.de/sitemap.aspx"]
    url_regex = r"https://www\.dominos\.de/+filiale/+[\w]+-[\w]+-([\d]+)$"
    sitemap_rules = [(url_regex, "parse_store")]
    custom_settings = {"DOWNLOAD_TIMEOUT": 180, "USER_AGENT": BROWSER_DEFAULT}

    def sitemap_filter(self, entries: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
        for entry in entries:
            entry["loc"] = re.sub(r"(\w)/+", r"\1/", entry["loc"])  # clean url pattern filiale//
            yield entry

    def parse_store(self, response: Response) -> Any:
        address_data = response.xpath('//a[@id="open-map-address"]/text()').getall()
        properties = {
            "ref": re.match(self.url_regex, response.url).group(1),
            "branch": response.xpath('//*[@class="storetitle"]/text()').get("").removeprefix("Domino's Pizza "),
            "street_address": clean_address(address_data[0].strip().strip(",")),
            "lat": response.xpath('//input[@id="store-lat"]/@value').get().replace(",", "."),
            "lon": response.xpath('//input[@id="store-lon"]/@value').get().replace(",", "."),
            "phone": response.xpath('//a[contains(@href, "tel:")]/@href').get(),
            "website": response.url,
        }
        if locality_data := re.match(r"([\d]+)? ?([-\ \w'À-Ÿ()]+)$", address_data[1].strip()):
            properties["city"] = locality_data.group(2)
            properties["postcode"] = locality_data.group(1)

        yield Feature(**properties)
