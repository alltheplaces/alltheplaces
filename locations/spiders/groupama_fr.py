import re

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider

POI_URL_RE = re.compile(r"\"webreseau\":\"(https://agences\.groupama\.fr/[^\"?]+-id[A-Z0-9]+)")
DEPARTMENT_URL_RE = re.compile(r"/agences-[-\w]+-r[0-9AB]+$")


class GroupamaFRSpider(StructuredDataSpider):
    name = "groupama_fr"
    item_attributes = {"brand": "Groupama", "brand_wikidata": "Q3083531"}
    allowed_domains = ["agences.groupama.fr"]
    start_urls = ["https://agences.groupama.fr/assurance/sitemap_agence_geo.xml"]
    wanted_types = ["InsuranceAgency"]
    drop_attributes = {"image"}
    # The pages only expose region-level (not agency-level) social accounts.
    search_for_twitter = False
    search_for_facebook = False

    def parse(self, response: Response, **kwargs):
        response.selector.remove_namespaces()
        for url in response.xpath("//loc/text()").getall():
            if DEPARTMENT_URL_RE.search(url):
                yield response.follow(url, self.parse_department)

    def parse_department(self, response: Response):
        for url in set(POI_URL_RE.findall(response.text)):
            yield response.follow(url, self.parse_sd)

    def post_process_item(self, item, response: Response, ld_data: dict, **kwargs):
        if isinstance(ld_data.get("@id"), str) and "location-" in ld_data["@id"]:
            item["ref"] = ld_data["@id"].rpartition("location-")[2]
        branch = (item.pop("name", None) or "").removeprefix("Agence Groupama").removeprefix(" De ").strip(" -")
        item["branch"] = branch or None
        apply_category(Categories.OFFICE_INSURANCE, item)
        yield item
