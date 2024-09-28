from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class PapaJohnsSpider(SitemapSpider, StructuredDataSpider):
    name = "papa_johns"
    item_attributes = {"brand": "Papa John's", "brand_wikidata": "Q2759586"}
    allowed_domains = ["papajohns.com"]
    sitemap_urls = ["https://locations.papajohns.com/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/locations\.papajohns\.com\/(?:united\-states|canada)\/\w{2}\/[-\w]+\/[-\w]+\/.+$",
            "parse_sd",
        )
    ]
    wanted_types = ["FastFoodRestaurant"]
    drop_attributes = {"image"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        if name := item.get("name", "").lower():
            if name.startswith("coming soon - "):
                return
            else:
                item["branch"] = item.pop("name").removeprefix("Papa Johns Pizza ")

        item["website"] = reseponse.urljoin(item["website"])

        yield item
