from typing import Iterable

from scrapy import Request
from scrapy.http import FormRequest, Response
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.items import Feature


class EasyfitnessDESpider(SitemapSpider):
    name = "easyfitness_de"
    item_attributes = {"brand": "EasyFitness", "brand_wikidata": "Q106166703"}
    sitemap_urls = ["https://easyfitness.club/robots.txt"]
    sitemap_rules = [
        (r"/studio/", "parse"),
    ]

    def _parse_sitemap(self, response: Response) -> Iterable[Request]:
        # Intercept the requests that result from parsing the sitemap. Instead of actually performing them, only look at
        # their URLs.
        for request in super()._parse_sitemap(response):
            if "/studio/" in request.url:
                slug = request.url.removesuffix("/").rsplit("/", maxsplit=1)[1]
                search_term = slug.removeprefix("easyfitness-").replace("-", " ").title()
                # The search API expects a search term like a city name or an address. Use the sitemap to get the names
                # of all gyms, then search for each of them.
                yield FormRequest(
                    "https://easyfitness.club/wp-admin/admin-ajax.php",
                    formdata={
                        "action": "search_nearby_studios",
                        "search_term": search_term,
                        "addaction": "start",
                    },
                )
            else:
                yield request

    def parse(self, response: Response, **kwargs) -> Iterable[Feature]:
        for data in response.json()["list"]:
            item = DictParser.parse(data)
            item["branch"] = item.pop("name").removeprefix("EASYFITNESS ")
            item["ref"] = data["link"].rstrip("/").split("/")[-1]
            item["postcode"], item["city"] = data.get("city").split(" ", maxsplit=1)
            item["street_address"] = item.pop("street")
            item["website"] = data["link"]
            yield item
