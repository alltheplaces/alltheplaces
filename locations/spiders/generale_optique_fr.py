import json

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class GeneraleOptiqueFRSpider(SitemapSpider, StructuredDataSpider):
    name = "generale_optique_fr"
    item_attributes = {
        "brand": "Générale d'Optique",
        "brand_wikidata": "Q62391701",
    }
    sitemap_urls = ["https://www.generale-optique.com/robots.txt"]
    sitemap_rules = [
        (r"/opticien/.*[0-9]+$", "parse_sd"),
    ]
    drop_attributes = ["image", "twitter", "facebook"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.SHOP_OPTICIAN, item)

        data = response.xpath("//script[contains(@id, '__NEXT_DATA__')]/text()").get()

        item["branch"] = (
            " ".join(item.pop("name", "").split())
            .lower()
            .removeprefix("opticien ")
            .removeprefix("et audioprothésiste ")
            .removeprefix("indépendant ")
            .removesuffix(" générale d'optique")
            .removeprefix("générale d'optique ")
            .removesuffix(" opticien")
        )

        if data:
            data = json.loads(data)
            store_data = (
                data.get("props", {})
                    .get("initialProps", {})
                    .get("pageProps", {})
                    .get("storeData")
            )

            if store_data:
                lat = store_data.get("lat")
                lon = store_data.get("lon")

                if lat is not None and lon is not None:
                    item["lat"] = str(lat)
                    item["lon"] = str(lon)
            
        yield item
