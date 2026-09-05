import re

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider

POI_URL_RE = re.compile(r"\"webreseau\":\"(https://agences\.groupama\.fr/[^\"?]+-id[A-Z0-9]+)")


class GroupamaFRSpider(SitemapSpider, StructuredDataSpider):
    name = "groupama_fr"
    item_attributes = {"brand": "Groupama", "brand_wikidata": "Q3083531"}
    allowed_domains = ["agences.groupama.fr"]
    sitemap_urls = ["https://agences.groupama.fr/assurance/sitemap_agence_geo.xml"]
    # The geo sitemap only lists region/department/city SEO pages. The per-agency
    # pages are linked (as "webreseau") from the department listings, so match
    # those and harvest the agency URLs from each.
    sitemap_rules = [(r"/agences-[-\w]+-r[0-9AB]+$", "parse_department")]
    wanted_types = ["InsuranceAgency"]
    drop_attributes = {"image"}
    # The pages only expose region-level (not agency-level) social accounts.
    search_for_twitter = False
    search_for_facebook = False

    def parse_department(self, response: Response):
        for url in set(POI_URL_RE.findall(response.text)):
            yield response.follow(url, self.parse_sd)

    def post_process_item(self, item, response: Response, ld_data: dict, **kwargs):
        if isinstance(ld_id := ld_data.get("@id"), str):
            _, marker, ref = ld_id.rpartition("location-")
            if marker and ref:
                item["ref"] = ref
        branch = (item.pop("name", None) or "").removeprefix("Agence Groupama").removeprefix(" De ").strip(" -")
        item["branch"] = branch or None
        apply_category(Categories.OFFICE_INSURANCE, item)
        yield item
