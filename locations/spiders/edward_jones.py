import scrapy
from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class EdwardJonesSpider(SitemapSpider, StructuredDataSpider):
    name = "edward_jones"
    item_attributes = {"brand": "Edward Jones", "brand_wikidata": "Q5343830"}
    allowed_domains = ["www.edwardjones.com"]
    sitemap_urls = ["https://www.edwardjones.com/us-en/sitemap/financial-advisor/sitemap.xml"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        oh = OpeningHours()
        oh.from_linked_data(ld_data, time_format="%H:%M:%S")
        item["opening_hours"] = oh.as_opening_hours()

        yield from self.get_location(item, 1)

    def get_location(self, item, page):
        url = "https://www.edwardjones.com/api/v3/financial-advisor/results?q={postcode}&distance=75&distance_unit=mi&page={page}&searchtype=2".format(
            postcode=item["postcode"], page=page
        )
        yield scrapy.Request(url=url, cb_kwargs={"item": item, "page": 1}, callback=self.parse_location)

    def parse_location(self, response, item, page):
        json = response.json()
        results = json["results"]

        for x in results:
            if item["website"].endswith(x["faUrl"]):
                item["lat"] = x["lat"]
                item["lon"] = x["lon"]
                break

        if ("lat" in item and "lon" in item) or json["resultCount" == 0] or len(results) < json["itemsPerPage"]:
            yield item
        else:
            yield from self.get_location(item, page + 1)
