from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.structured_data_spider import StructuredDataSpider


class CaliforniaClosetsSpider(SitemapSpider, StructuredDataSpider):
    name = "california_closets"
    item_attributes = {
        "brand_wikidata": "Q5020325",
        "brand": "California Closets",
    }
    sitemap_urls = [
        "https://www.locations.californiaclosets.com/sitemap.xml",
        "https://www.locations.californiaclosets.ca/sitemap.xml",
    ]
    sitemap_rules = [
        (r"locations.californiaclosets.com/california-closets-[-\w]+-[-0-9a-f]+$", "parse_sd"),
        (r"locations.californiaclosets.ca/[a-z]{2}/[-\w]+/[-\w]+-showroom", "parse_sd"),
    ]
    wanted_types = ["LocalBusiness", "ProfessionalService"]
    drop_attributes = {"image", "twitter"}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        website = ld_data.get("url")
        if website and website != response.url:  # Skip nearby locations to avoid duplicates
            return
        item["ref"] = website or response.url
        item["branch"] = (
            item.pop("name")
            .replace("California Closets", "")
            .split("|")[0]
            .strip()
            .removeprefix("-")
            .removesuffix(" Showroom")
        )
        item["country"] = response.xpath("//@data-country").get()
        if not item.get("street_address"):
            item["street_address"] = merge_address_lines(
                [
                    response.xpath('//*[@class="c-address-street-1"]/text()').get(""),
                    response.xpath('//*[@class="c-address-street-2"]/text()').get(""),
                ]
            )
            item["city"] = response.xpath('//*[@class="c-address-city"]/text()').get()
            item["state"] = response.xpath('//*[@class="c-address-state"]/text()').get()
            item["postcode"] = response.xpath('//*[@class="c-address-postal-code"]/text()').get()
        yield item
