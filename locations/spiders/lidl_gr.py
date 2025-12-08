from locations.hours import DAYS_GR
from locations.spiders.lidl_at import LidlATSpider


class LidlGRSpider(LidlATSpider):
    name = "lidl_gr"

    dataset_id = "c1070f3f97ad43c7845ab237eef704c0"
    dataset_name = "Filialdaten-GR/Filialdaten-GR"
    api_key = "AjbddE6Qo-RdEfEZ74HKQxTGiCSM4dEoDL5uGGCiw7nOWaQiaKWSzPoGpezAfY_x"
    days = DAYS_GR
