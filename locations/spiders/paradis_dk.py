from scrapy.spiders import SitemapSpider

from locations.categories import apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class ParadisDKSpider(SitemapSpider):
    name = "paradis_dk"
    item_attributes = {"brand": "Paradis", "brand_wikidata": "Q12330951"}
    sitemap_urls = ["https://paradis-is.dk/wp-sitemap.xml"]
    sitemap_follow = ["butikker"]
    sitemap_rules = [(r"", "parse")]

    def parse(self, response, **kwargs):
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["name"] = response.xpath("//title/text()").get()
        if address := response.xpath('//*[contains(text(),"adresse")]/following-sibling::p[1]/text()').getall():
            item["addr_full"] = merge_address_lines(address)
        else:
            item["addr_full"] = merge_address_lines(
                response.xpath('//*[contains(@class,"title-info")]/p[1]/text()').getall()
            )
        item["email"] = (
            response.xpath('//a[contains(@href, "mailto")]/@href').get().replace("mailto:", "") or "info@paradis-is.dk"
        )
        apply_category({"shop": "ice_cream"}, item)

        yield item
