import scrapy

from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class ErbertAndGerbertsSpider(scrapy.Spider):
    name = "erbert_and_gerberts"
    item_attributes = {"brand": "Erbert & Gerbert's", "brand_wikidata": "Q5385097"}
    allowed_domains = ["erbertandgerberts.com"]
    start_urls = ["https://www.erbertandgerberts.com/store-sitemap.xml"]
    user_agent = BROWSER_DEFAULT

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath("//url/loc/text()").extract()
        for path in city_urls:
            yield scrapy.Request(
                path.strip(),
                callback=self.parse_store,
            )

    def parse_store(self, response):
        properties = {
            "name": response.xpath('//h1[@class="ph__title text-cursive mb0"]/text()').extract_first(),
            "ref": response.xpath('//h1[@class="ph__title text-cursive mb0"]/text()').extract_first(),
            "street_address": response.xpath("//address[@class]/text()").extract_first(),
            "city": response.xpath("//address[@class]/text()").extract()[1].split(",")[0],
            "state": response.xpath("//address[@class]/text()").extract()[1].split()[-2],
            "postcode": response.xpath("//address[@class]/text()").extract()[1].split()[-1],
            "phone": response.xpath('//div[@class="store__contact text-gray std-mb"]/p/a/text()').extract_first(),
            "website": response.request.url,
            "lat": response.xpath("//div/main/div/div/div/div/script/text()")
            .extract_first()
            .split("lat")[1]
            .strip()
            .split('"')[1],
            "lon": response.xpath("//div/main/div/div/div/div/script/text()")
            .extract_first()
            .split("lng")[1]
            .strip()
            .split('"')[1],
        }

        yield Feature(**properties)
