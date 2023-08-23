from scrapy.spiders import SitemapSpider

from locations.items import Feature


class InteriorHealthCASpider(SitemapSpider):
    name = "interior_health_ca"
    item_attributes = {"brand": "Interior Health", "brand_wikidata": "Q6046681"}
    allowed_domains = ["www.interiorhealth.ca"]
    sitemap_urls = ["https://www.interiorhealth.ca/sitemap.xml"]
    sitemap_rules = [("/locations/", "parse")]

    def parse(self, response):
        properties = {
            "ref": response.url,
            "name": response.xpath('//div[contains(@class, "top-banner-header-content")]/h1/text()').get().strip(),
            "lat": response.xpath("//@data-lat").get(),
            "lon": response.xpath("//@data-lng").get(),
            "street_address": response.xpath('//span[@class="address-line1"]/text()').get().strip(),
            "city": response.xpath('//span[@class="locality"]/text()').get().strip(),
            "state": response.xpath('//span[@class="administrative-area"]/text()').get().strip(),
            "postcode": response.xpath('//span[@class="postal-code"]/text()').get().strip(),
            "phone": response.xpath('//li[@class="location-item"]/a[contains(@href, "tel:")]/@href').get(),
            "website": response.url,
        }
        if properties["phone"]:
            properties["phone"] = properties["phone"].replace("tel:", "").strip()
        else:
            properties.pop("phone", None)
        yield Feature(**properties)
