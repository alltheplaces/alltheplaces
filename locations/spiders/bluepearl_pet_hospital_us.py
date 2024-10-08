from scrapy import Selector
from scrapy.spiders import SitemapSpider

from locations.hours import DAYS, OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class BluepearlPetHospitalUSSpider(SitemapSpider, StructuredDataSpider):
    name = "bluepearl_pet_hospital_us"
    item_attributes = {"brand": "BluePearl Pet Hospital", "brand_wikidata": "Q4928764"}
    allowed_domains = ["bluepearlvet.com"]
    sitemap_urls = ["https://bluepearlvet.com/hospital-sitemap.xml"]
    sitemap_rules = [(r"\/hospital\/[\w\-]+\/$", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    requires_proxy = True  # Cloudflare bot protection used

    def post_process_item(self, item, response, ld_data):
        name_html = Selector(text=ld_data["name"])
        item["name"] = " ".join((" ".join(name_html.xpath("//text()").getall())).split()).replace(
            " - BluePearl Pet Hospital", ""
        )
        item.pop("twitter")
        item.pop("facebook")
        if "24/7" in ld_data["openingHours"]:
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_days_range(DAYS, "00:00", "23:59")
        # else: not worth parsing because not even humans can interpret the
        # unintelligible hours information (example: "Sun 7am-Thu 6 am")
        yield item
