from scrapy import Request

from locations.structured_data_spider import StructuredDataSpider


class SbarroSpider(StructuredDataSpider):
    name = "sbarro"
    item_attributes = {"brand": "Sbarro", "brand_wikidata": "Q2589409"}
    allowed_domains = ["sbarro.com"]
    start_urls = ["https://sbarro.com/locations/?user_search=78749&radius=50000&count=5000"]
    wanted_types = ["Restaurant"]

    def parse(self, response):
        store_urls = response.xpath('//*[@class="location-name "]/a/@href').extract()
        ids = response.xpath('//*[@class="locations-result"]/@id').extract()
        lats = response.xpath('//*[@class="locations-result"]/@data-latitude').extract()
        longs = response.xpath('//*[@class="locations-result"]/@data-longitude').extract()

        for store_url, id, lat, long in zip(store_urls, ids, lats, longs):
            store_url = "https://sbarro.com" + store_url + "/"
            yield Request(
                response.urljoin(store_url),
                callback=self.parse_sd,
                meta={"lat": lat, "lon": long, "ref": id},
            )

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = response.meta["ref"]
        item["branch"] = response.xpath('//*[@class="location-name "]/text()').get()
        item["name"] = None
        item["lat"] = response.meta["lat"]
        item["lon"] = response.meta["lon"]
        yield item
