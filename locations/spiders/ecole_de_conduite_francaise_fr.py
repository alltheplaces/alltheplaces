from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider, clean_facebook
from locations.categories import Categories, apply_category
import json
import scrapy

class EcoleDeConduiteFrancaiseFRSpider(CrawlSpider, StructuredDataSpider):
    name = "ecole_de_conduite_francaise_fr"
    item_attributes = {
        "brand": "ECF",
        "brand_wikidata": "Q114870266",
    }
    allowed_domains = ["www.ecf.asso.fr"]
    start_urls = ["https://www.ecf.asso.fr/grand-public-carte"]
    drop_attributes = ["image"]

    def parse_start_url(self, response):
        data = response.xpath("//*[@*[name() = 'wire:snapshot' and contains(., 'markers')]]/@*[name() = 'wire:snapshot']").get()
                
        data = json.loads(data)

        for marker in data["data"]["markers"]:
            if isinstance(marker,list):
                for m in marker:
                    for elem in m:
                        if "title" in list(elem.keys()):
                            title = elem["title"]
                            if title != "":
                                slug = "-".join(
                                    title
                                    .lower()
                                    .replace("\u00e9","e")
                                    .replace("\u00ea","e")
                                    .replace(" - ","-")
                                    .replace(" / "," ")
                                    .replace(" + "," ")
                                    .replace("/","")
                                    .replace("'","")
                                    .replace(",","")
                                    .strip()
                                    .split(" "))
                                if("orakin" in slug):
                                    slug = slug.removeprefix("auto-ecole-").removeprefix("ecf-")
                                    slug = "ecf-llerena-ecf-" + slug

                                if("ecf-ariege-" in slug):
                                    slug.replace("ecf-ariege-","ecf-drive-formation-")
                                
                                yield scrapy.Request(
                                    "https://www.ecf.asso.fr/agence/" + slug,
                                    callback=self.parse_sd,
                                )

                                if slug.startswith("auto-ecole-"):
                                    yield scrapy.Request(
                                        "https://www.ecf.asso.fr/agence/" + slug.removeprefix("auto-ecole-"),
                                    callback=self.parse_sd,
                                )

    def post_process_item(self, item, response, ld_data):
        apply_category(Categories.DRIVING_SCHOOL, item)
        item["branch"] = item.pop("name", "").removeprefix("Auto-école ").removeprefix("Piste moto ").removeprefix("ECF ")

        item["facebook"] = clean_facebook(item.get("facebook"))
        if item["facebook"] in ["https://www.facebook.com/groupe.ecf/","https://www.facebook.com/ECFGROUPESPS","https://www.facebook.com/ECFGROUPESPS/"]:
            item["facebook"] = None

        yield item
