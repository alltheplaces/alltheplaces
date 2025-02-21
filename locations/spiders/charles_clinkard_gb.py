import scrapy

#from locations.hours import OpeningHours
from locations.items import Feature


class CharlesClinkardGBSpider(scrapy.Spider):
    name = "charles_clinkard_gb"
    item_attributes = {"brand": "Charles Clinkard",}
    allowed_domains = [
        "www.charlesclinkard.co.uk",
    ]
    start_urls = ("https://www.charlesclinkard.co.uk/map",)

    def parse(self, response):
        urls = response.xpath('//a[@class="store-locator__store__link button"]/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_store)

    def parse_store(self, response):
        #oh = OpeningHours()

        properties = {
            "branch": response.xpath('//h1/text()').extract_first(),
            "addr_full": ", ".join(response.xpath('//div[@class="col l-col-16 store-locator__store__col"]/div/p/span/text()').extract()),
            "phone": response.xpath('//a[contains(@href, "tel:")]/text()').extract_first(),
            "ref": response.url.replace("https://www.charlesclinkard.co.uk/map/",""),
            "website": response.url,
            #"lat": response.xpath('//script[contains("var myLatlng")]').extract_first(),
            #"lon": response.xpath('normalize-space(//meta[@itemprop="longitude"]/@content)').extract_first(),
            #"opening_hours": oh.as_opening_hours(),
        }
        yield Feature(**properties)
