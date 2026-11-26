from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class JeffDeBrugesSpider(SitemapSpider, StructuredDataSpider):
    name = "jeff_de_bruges"
    item_attributes = {"brand": "Jeff de Bruges", "brand_wikidata": "Q3176626"}
    sitemap_urls = ["https://www.jeff-de-bruges.com/Assets/Rbs/Seo/sitemap-index.xml"]
    sitemap_follow = ["en_US/Rbs_Store_Store"]
    time_format = "%H:%M:%S"
    custom_settings = {"DOWNLOAD_TIMEOUT": 180}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Jeff de Bruges ")

        item["extras"]["website:fr"] = response.xpath('//link[@rel="alternate"][@hreflang="fr-FR"]/@href').get()
        item["extras"]["website:en"] = response.xpath('//link[@rel="alternate"][@hreflang="en-US"]/@href').get()
        apply_category(Categories.SHOP_CHOCOLATE, item)
        yield item
