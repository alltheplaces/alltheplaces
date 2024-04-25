from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BanfieldPetHospitalSpider(SitemapSpider, StructuredDataSpider):
    name = "banfield_pet_hospital"
    item_attributes = {"brand": "Banfield Pet Hospital", "brand_wikidata": "Q2882416"}
    drop_attributes = {"image"}
    allowed_domains = ["www.banfield.com"]
    sitemap_urls = ["https://www.banfield.com/robots.txt"]
    sitemap_rules = [(r"/locations/veterinarians/\w\w/[-\w]+/\w\w\w$", "parse_sd")]
    wanted_types = [["VeterinaryCare", "LocalBusiness"]]
