from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.user_agents import BROWSER_DEFAULT


class DominosPizzaFRSpider(SitemapSpider):
    name = "dominos_pizza_fr"
    item_attributes = {"brand": "Domino's", "brand_wikidata": "Q839466"}
    allowed_domains = ["dominos.fr"]
    user_agent = BROWSER_DEFAULT
    sitemap_urls = ["https://www.dominos.fr/sitemap.aspx"]
    sitemap_rules = [(r"https:\/\/www\.dominos\.fr\/magasin\/\/?([-\w.]+)_(unknown|[\d]+)$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        properties = {
            "ref": response.url,
            "branch": response.xpath('//h1[@class="storetitle"]/text()').get().removeprefix("Domino's Pizza "),
            "addr_full": clean_address(response.xpath('//a[@id="open-map-address"]/text()').get()),
            "lat": response.xpath('//input[@id="store-lat"]/@value').get().replace(",", "."),
            "lon": response.xpath('//input[@id="store-lon"]/@value').get().replace(",", "."),
            "phone": response.xpath('//div[@class="store-phone"]/a/text()').get(),
            "website": response.url,
        }

        apply_category(Categories.FAST_FOOD, properties)

        yield Feature(**properties)
