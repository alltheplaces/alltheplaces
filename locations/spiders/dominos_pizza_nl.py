import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class DominosPizzaNLSpider(SitemapSpider):
    name = "dominos_pizza_nl"
    item_attributes = {"brand": "Domino's", "brand_wikidata": "Q839466"}
    allowed_domains = ["dominos.nl"]
    sitemap_urls = ["https://www.dominos.nl/sitemap.aspx"]
    url_regex = r"https://www\.dominos\.nl/+winkel/+[\w]+-[\w]+-([\d]+)$"
    sitemap_rules = [(url_regex, "parse_store")]
    user_agent = BROWSER_DEFAULT

    def sitemap_filter(self, entries: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
        for entry in entries:
            entry["loc"] = re.sub(r"(\w)/+", r"\1/", entry["loc"])
            yield entry

    def parse_store(self, response: Response) -> Any:
        address_data = response.xpath('//a[@id="open-map-address"]/text()').getall()
        locality_data = re.search(r"(.*) ([A-Z]{2}) (.*)", address_data[1].strip())
        properties = {
            "ref": re.match(self.url_regex, response.url).group(1),
            "branch": response.xpath('//*[@class="storetitle"]/text()').get("").removeprefix("Domino's Pizza "),
            "street_address": address_data[0].strip().strip(","),
            "lat": response.xpath('//input[@id="store-lat"]/@value').get().replace(",", "."),
            "lon": response.xpath('//input[@id="store-lon"]/@value').get().replace(",", "."),
            "phone": response.xpath('//a[contains(@href, "tel:")]/@href').get(),
            "website": response.url,
        }
        if locality_data:
            properties["city"] = locality_data.group(1)
            properties["postcode"] = locality_data.group(3)
        yield Feature(**properties)
