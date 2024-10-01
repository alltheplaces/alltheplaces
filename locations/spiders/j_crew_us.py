from scrapy.spiders import SitemapSpider

from locations.categories import apply_yes_no
from locations.structured_data_spider import StructuredDataSpider


class JCrewUSSpider(SitemapSpider, StructuredDataSpider):
    name = "j_crew_us"
    item_attributes = {"brand": "J. Crew", "brand_wikidata": "Q5370765"}
    allowed_domains = ["jcrew.com"]
    sitemap_urls = ["https://stores.jcrew.com/robots.txt", "https://stores.factory.jcrew.com/robots.txt"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name")
        if "stores.factory.jcrew.com" in response.url:
            item["name"] = "J.Crew Factory"
            apply_yes_no("factory_outlet", item, True)
        else:
            item["name"] = "J.Crew"

        item["phone"] = response.xpath('//div[@id="phone-main"]/a/@href').get()

        yield item
    drop_attributes = {"image"}
