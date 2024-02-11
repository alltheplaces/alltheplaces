from scrapy.spiders import SitemapSpider

from locations.categories import apply_category
from locations.items import set_closed
from locations.structured_data_spider import StructuredDataSpider


class FreseniusKidneyCareUSSpider(SitemapSpider, StructuredDataSpider):
    name = "fresenius_kidney_care_us"
    item_attributes = {"operator": "Fresenius Kidney Care", "operator_wikidata": "Q650259"}
    download_delay = 0.2
    sitemap_urls = ["https://www.freseniuskidneycare.com/robots.txt"]
    sitemap_follow = ["center"]
    sitemap_rules = [(r"/dialysis-centers/[-\w]+/\w+$", "parse_sd")]
    wanted_types = ["MedicalClinic"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category({"amenity": "clinic", "healthcare": "dialysis", "healthcare:speciality": "nephrology"}, item)

        if item["name"].endswith("- Closed") or item["name"].endswith(" (Closed)"):
            set_closed(item)

        yield item
