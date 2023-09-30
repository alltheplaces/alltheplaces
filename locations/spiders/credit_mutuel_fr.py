from scrapy import Request, Spider

from locations.categories import Categories, apply_category
from locations.items import Feature


class CreditMutuelFRSpider(Spider):
    name = "credit_mutuel_fr"
    item_attributes = {"brand": "Crédit Mutuel", "brand_wikidata": "Q642627"}
    allowed_domains = ["www.creditmutuel.fr"]
    start_urls = ["https://www.creditmutuel.fr/fr/sitemap-cm-caisses.txt"]
    custom_settings = {"REDIRECT_ENABLED": False}

    def parse(self, response):
        for url in response.text.splitlines():
            if url[-7:] != "/00/000":
                continue
            yield Request(url=url, callback=self.parse_location)

    def parse_location(self, response):
        properties = {
            "ref": "".join(response.xpath('.//span[@itemprop="branchCode"]/text()').getall()).strip(),
            "name": "".join(response.xpath(".//title/text()").getall()).strip(),
            "lat": response.xpath('.//meta[@itemprop="latitude"]/@content').get(),
            "lon": response.xpath('.//meta[@itemprop="longitude"]/@content').get(),
            "street_address": "".join(response.xpath('.//span[@itemprop="streetAddress"]/text()').getall()).strip(),
            "city": "".join(response.xpath('.//span[@itemprop="addressLocality"]/text()').getall()).strip(),
            "postcode": "".join(response.xpath('.//span[@itemprop="postalCode"]/text()').getall()).strip(),
            "phone": "".join(response.xpath('(.//span[@itemprop="telephone"])[1]/text()').getall()).strip(),
            "email": response.xpath('.//a[@class="popmail"]/@href').get(default="").replace("mailto:", ""),
            "website": response.url,
        }
        apply_category(Categories.BANK, properties)
        # Opening Hours can't be extracted because the HTML is
        # invalid and includes a <table />, hence any nested cells
        # containing opening hours information can't be selected
        # via XPath nor CSS selectors.
        yield Feature(**properties)
