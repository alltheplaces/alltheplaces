from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class DieselSpider(SitemapSpider, StructuredDataSpider):
    name = "diesel"
    item_attributes = {"brand": "Diesel", "brand_wikidata": "Q158285"}
    sitemap_urls = ["https://uk.diesel.com/en/sitemap-stores-en-gb.xml"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if email := item.get("email"):
            item["email"] = email.replace(" ", "")

        if item["name"].startswith("DIESEL ACCESSORIES STORE "):
            item["branch"] = item.pop("name").removeprefix("DIESEL ACCESSORIES STORE ")
            item["name"] = "Diesel Accessories"
        elif item["name"].startswith("DIESEL KID OUTLET "):
            item["branch"] = item.pop("name").removeprefix("DIESEL KID OUTLET ")
            item["name"] = "Diesel Kid Outlet"
        elif item["name"].startswith("DIESEL KID STORE "):
            item["branch"] = item.pop("name").removeprefix("DIESEL KID STORE ")
            item["name"] = "Diesel Kid"
        elif item["name"].startswith("DIESEL MENSWEAR STORE "):
            item["branch"] = item.pop("name").removeprefix("DIESEL MENSWEAR STORE ")
            item["name"] = "Diesel Menswear"
        elif item["name"].startswith("DIESEL OUTLET "):
            item["branch"] = item.pop("name").removeprefix("DIESEL OUTLET ")
            item["name"] = "Diesel Outlet"
        elif item["name"].startswith("DIESEL STORE "):
            item["branch"] = item.pop("name").removeprefix("DIESEL STORE ")
            item["name"] = "Diesel"
        elif item["name"].startswith("DIESEL WOMENSWEAR STORE "):
            item["branch"] = item.pop("name").removeprefix("DIESEL WOMENSWEAR STORE ")
            item["name"] = "Diesel Womenswear"
        else:
            item["branch"] = item.pop("name").removeprefix("DIESEL ")
        yield item
