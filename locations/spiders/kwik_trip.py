import scrapy
from locations.items import GeojsonPointItem


class KwikTripSpider(scrapy.Spider):
    name = "kwiktrip"
    item_attributes = {"brand": "Kwik Trip", "brand_wikidata": "Q6450420"}
    allowed_domains = ["www.kwiktrip.com"]
    download_delay = 0
    user_agent = (
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/63.0.3239.84 Safari/537.36"
    )
    start_urls = ("https://www.kwiktrip.com/Maps-Downloads/Store-List",)

    def parse(self, response):
        rows = response.xpath("(//tr)[position()>1]")  # Skip header of table

        for row in rows:
            properties = {
                "ref": row.xpath('.//td[@class="column-1"]/text()').extract_first(),
                "name": row.xpath('.//td[@class="column-2"]/text()').extract_first(),
                "addr_full": row.xpath(
                    './/td[@class="column-3"]/text()'
                ).extract_first(),
                "city": row.xpath('.//td[@class="column-4"]/text()').extract_first(),
                "state": row.xpath('.//td[@class="column-5"]/text()').extract_first(),
                "postcode": row.xpath(
                    './/td[@class="column-6"]/text()'
                ).extract_first(),
                "lat": row.xpath('.//td[@class="column-8"]/text()').extract_first(),
                "lon": row.xpath('.//td[@class="column-9"]/text()').extract_first(),
                "phone": row.xpath('.//td[@class="column-7"]/text()').extract_first(),
                "website": response.url,
            }

            yield GeojsonPointItem(**properties)
