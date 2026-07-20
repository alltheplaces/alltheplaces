from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.items import Feature


class EspacolaserBRSpider(SitemapSpider):
    name = "espacolaser_br"
    item_attributes = {
        "brand": "Espaçolaser",
        "brand_wikidata": "Q112326409",
    }
    sitemap_urls = ["https://espacolaser.com.br/sitemap.xml"]
    sitemap_rules = [("/unidade", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["branch"] = response.xpath("//h1/text()").get()
        item["street_address"] = response.xpath('//*[@class="col enderecos"]//p//text()').get()
        item["ref"] = item["website"] = response.url
        item["phone"] = response.xpath('//*[@class="col contatos"]//p//text()').get()
        extract_google_position(item, response)
        yield item
