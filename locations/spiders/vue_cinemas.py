from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class VueCinemasSpider(SitemapSpider):
    name = "vue_cinemas"
    item_attributes = {"brand": "Vue", "brand_wikidata": "Q2535134"}
    sitemap_urls = ["https://www.myvue.com/sitemap.xml"]
    sitemap_rules = [(r"/getting-here$", "parse")]

    def parse(self, response, **kwargs):
        item = Feature()
        item["ref"] = response.xpath("//@data-selected-locationid").get()
        item["name"] = response.xpath("//@data-selected-locationname").get()
        item["website"] = response.url.replace("/getting-here", "")

        cinema = response.xpath('//div[@data-scroll-id="cinema-details"]')

        address_parts = cinema.xpath('.//img[@alt="location-pin"]/../text()').getall()
        if not address_parts:
            address_parts = cinema.xpath(
                './/div[contains(@data-page-url, "/getting-here")]/following-sibling::div//div[@class="container container--scroll"]/div/p/text()'
            ).getall()

        item["addr_full"] = merge_address_lines(address_parts)

        extract_google_position(item, cinema)

        yield item
