from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.items import GeojsonPointItem
from locations.structured_data_spider import extract_email, extract_phone


class OxfamGBSpider(SitemapSpider):
    name = "oxfam_gb"
    item_attributes = {"brand": "Oxfam", "brand_wikidata": "Q267941", "country": "GB"}
    sitemap_urls = ["https://www.oxfam.org.uk/sitemap.xml"]
    sitemap_rules = [("/shops/oxfam-", "parse_shop")]
    download_delay = 0.5

    def parse_shop(self, response):
        item = GeojsonPointItem()
        item["website"] = item["ref"] = response.url
        item["street_address"] = response.xpath(
            '//*[@class="shop-address"]/li/text()'
        ).get()
        item["city"] = response.xpath('//*[@class="shop-address"]/li[2]/text()').get()
        item["postcode"] = response.xpath(
            '//*[@class="shop-address"]/li[3]/text()'
        ).get()

        extract_google_position(item, response)
        extract_email(item, response)
        extract_phone(item, response)

        yield item
