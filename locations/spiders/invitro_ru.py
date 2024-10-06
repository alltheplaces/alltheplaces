from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class InvitroRUSpider(SitemapSpider, StructuredDataSpider):
    name = "invitro_ru"
    item_attributes = {"brand": "Инвитро", "brand_wikidata": "Q4200546"}
    sitemap_urls = ["https://www.invitro.ru/sitemap/offices.xml"]
    sitemap_rules = [(r"/offices/.*/clinic.php\?ID=.*", "parse_sd")]
    wanted_types = ["MedicalBusiness"]
    json_parser = "chompjs"
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = None
        coords = response.xpath('//div[@id="mapOfficeDetail"]/@data-coord').get()
        if coords:
            item["lat"], item["lon"] = coords.strip().split(",")
        apply_category(Categories.MEDICAL_LABORATORY, item)
        yield item
