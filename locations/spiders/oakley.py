import json
from urllib.parse import unquote

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category, apply_yes_no
from locations.structured_data_spider import StructuredDataSpider


class OakleySpider(SitemapSpider, StructuredDataSpider):
    name = "oakley"
    item_attributes = {
        "brand": "Oakley",
        "brand_wikidata": "Q161906",
    }
    sitemap_urls = ["https://stores.oakley.com/sitemap1.xml"]
    sitemap_rules = [
        (r"https://stores.oakley.com/[a-z]{2}/[\w.-]+/[\w.-]+/[\w.-]+", "parse"),
    ]
    search_for_email = False
    search_for_facebook = False
    search_for_twitter = False

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.SHOP_OPTICIAN, item)

        prefix = "pageProps: JSON.parse(decodeURIComponent("
        script = response.xpath(f"//script[contains(text(), {prefix!r})]/text()").get()
        if script is None:
            self.logger.error("Can't find JSON data in page, coordinates might be missing")
        else:
            start = script.find(prefix) + len(prefix)
            end = script.find(")),\n", start)
            initial_data = json.loads(unquote(json.loads(script[start:end])))
            document = initial_data["document"]

            item["branch"] = document.get("address", {}).get("extraDescription")
            item["image"] = document.get("c_locationPhoto", {}).get("image", {}).get("url")
            item["ref"] = document.get("id", response.url)
            item["lat"] = document.get("yextDisplayCoordinate", {}).get("latitude")
            item["lon"] = document.get("yextDisplayCoordinate", {}).get("longitude")

        yield item

    def extract_payment_accepted(self, item, response, ld_item):
        if "paymentAccepted" not in ld_item:
            return
        if "TRAVELERSCHECK" in ld_item["paymentAccepted"]:
            ld_item["paymentAccepted"].remove("TRAVELERSCHECK")
            apply_yes_no("payment:travellers_cheque", item, True)
        super().extract_payment_accepted(item, response, ld_item)
