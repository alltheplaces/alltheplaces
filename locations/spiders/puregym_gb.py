from urllib.parse import parse_qs, urlparse

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class PureGymGBSpider(SitemapSpider, StructuredDataSpider):
    name = "puregym_gb"
    item_attributes = {"brand": "PureGym", "brand_wikidata": "Q18345898", "country": "GB"}
    allowed_domains = ["www.puregym.com"]
    sitemap_urls = ["https://www.puregym.com/sitemap.xml"]
    sitemap_rules = [(r"/gyms/([^/]+)/$", "parse_sd")]
    wanted_types = ["HealthClub"]

    def pre_process_data(self, ld_data, **kwargs):
        ld_data["address"] = ld_data.get("location", {}).get("address")

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name")
        item["image"] = None

        if img := response.xpath('//img[contains(@src, "tiles.stadiamaps.com")]/@src').get():
            q = parse_qs(urlparse(img)[4])
            if "center" in q:
                item["lat"], item["lon"] = q["center"][0].split(",", 1)

        yield item
