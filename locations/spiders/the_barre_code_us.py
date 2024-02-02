from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.google_url import extract_google_position
from locations.items import Feature


class TheBarreCodeUSSpider(SitemapSpider):
    name = "the_barre_code_us"
    item_attributes = {
        "brand": "The Barre Code",
        "brand_wikidata": "Q118870170",
        "extras": Categories.GYM.value,
    }
    allowed_domains = ["thebarrecode.com"]
    sitemap_urls = ["https://thebarrecode.com/all-sitemap.xml"]
    sitemap_rules = [(r"thebarrecode.com\/(?!base-site)[\w\-]+\/contact-us\/?$", "parse")]

    def parse(self, response):
        properties = {
            "name": response.xpath('//span[@id="site_title"]/text()').get().strip(),
            "phone": response.xpath('//div[@class="info-container"]/div/div[1]//a[contains(@href, "tel:")]/@href')
            .get()
            .strip(),
            "addr_full": ", ".join(
                filter(None, response.xpath('//div[@class="info-container"]/div/div[2]//p/text()').getall())
            ).strip(),
            "email": response.xpath('//div[@class="info-container"]/div/div[4]//p/text()').get().strip(),
            "website": response.url.replace("/contact-us/", "/"),
            "ref": response.url.replace("/contact-us/", "/"),
        }
        extract_google_position(properties, response)
        yield Feature(**properties)
