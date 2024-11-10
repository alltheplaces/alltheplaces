
from locations.spiders.slim_chickens_gb import SlimChickensGBSpider

class GBKGBSpider(SlimChickensGBSpider):
    name = "gbk_gb"
    item_attributes = {"brand": "GBK", "brand_wikidata": "Q5588445"}
    start_urls = ["https://www.gbk.co.uk/find-your-gbk"]
