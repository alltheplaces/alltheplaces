from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser


class ExtraSpaceStorageUSSpider(SitemapSpider):
    name = "extra_space_storage_us"
    item_attributes = {"brand": "Extra Space Storage", "brand_wikidata": "Q5422162"}
    allowed_domains = ["www.extraspace.com"]
    sitemap_urls = ["https://www.extraspace.com/facility-sitemap.xml"]
    custom_settings = {"DOWNLOAD_TIMEOUT": 120}

    # Store pages become inaccessible because of bot-detection mechanism after a small number of successful requests (typically around 40), while the API continues to function normally.
    def sitemap_filter(self, entries: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
        for entry in entries:
            if "/facilities/" in entry["loc"]:
                slug = entry["loc"].strip("/").rsplit("/", 1)[-1]
                entry["loc"] = f"https://www.extraspace.com/api/phoenix/web-api/store/{slug}/"
                yield entry

    def parse(self, response: Response, **kwargs: Any) -> Any:
        store = response.json()["facilityData"]["data"]["store"]
        store.update(store.pop("geocode"))
        item = DictParser.parse(store)
        item["ref"] = store["ozStoreId"]
        item["branch"] = item.pop("name").split(" - ", 1)[-1]
        item["website"] = (
            f'https://www.extraspace.com/storage/facilities/us/{item["state"]}/{item["city"]}/{item["ref"]}/'.replace(
                " ", "_"
            ).lower()
        )
        yield item
