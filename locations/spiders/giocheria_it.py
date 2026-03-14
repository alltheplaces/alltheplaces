import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class GiocheriaITSpider(SitemapSpider):
    name = "giocheria_it"
    item_attributes = {"brand": "Giocheria", "brand_wikidata": "Q126032681"}
    sitemap_urls = ["https://giocheria.it/stores-sitemap.xml"]

    def parse(self, response, **kwargs):
        if "trova-negozio" not in response.url:
            item = Feature()
            item["branch"] = (
                response.xpath("//title/text()")
                .get()
                .replace("Giocheria", "")
                .replace("GIOCHERIA", "")
                .lstrip()
                .rstrip()
                .rstrip("-")
            )
            item["phone"] = response.xpath('//*[contains(@href,"tel:")]/text()').get()
            item["email"] = response.xpath('//*[contains(@href,"mailto:")]/text()').get()
            item["street_address"] = response.xpath(
                '//*[@id="main-content"]//*[@class="et_pb_text_inner"]/text()'
            ).get()
            item["addr_full"] = clean_address(
                ",".join(
                    response.xpath(
                        '//*[@class="et_pb_row et_pb_row_1_tb_body"]//div[1]//*[@class="et_pb_text_inner"]//text()'
                    ).getall()
                )
                .replace("Indirizzo:", "")
                .replace("Contatti:", "")
            )
            item["ref"] = item["website"] = response.url
            coords = re.search(r"q=(\d+\.\d+)\s*,\s*(\d+\.\d+)", response.xpath("//iframe/@src").get())
            if coords:
                item["lat"] = coords.group(1)
                item["lon"] = coords.group(2)
            apply_category(Categories.SHOP_TOYS, item)

            yield item
