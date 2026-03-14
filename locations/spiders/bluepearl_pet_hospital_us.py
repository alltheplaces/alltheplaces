from scrapy import Selector
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BluepearlPetHospitalUSSpider(SitemapSpider, StructuredDataSpider):
    name = "bluepearl_pet_hospital_us"
    item_attributes = {"brand": "BluePearl", "brand_wikidata": "Q4928764"}
    allowed_domains = ["bluepearlvet.com"]
    sitemap_urls = ["https://bluepearlvet.com/hospital-sitemap.xml"]
    sitemap_rules = [(r"\/hospital\/[\w\-]+\/$", "parse_sd")]
    wanted_types = ["LocalBusiness"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        name_html = Selector(text=ld_data["name"])
        item["name"] = " ".join((" ".join(name_html.xpath("//text()").getall())).split()).replace(
            " - BluePearl Pet Hospital", ""
        )
        item.pop("twitter")
        item.pop("facebook")
        yield item
