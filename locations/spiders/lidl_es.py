from locations.hours import DAYS_ES
from locations.spiders.lidl_at import LidlATSpider


class LidlESSpider(LidlATSpider):
    name = "lidl_es"

    dataset_id = "b5843d604cd14b9099f57cb23a363702"
    dataset_name = "Filialdaten-ES/Filialdaten-ES"
    api_key = "AjhJAzQQN7zhpMcZcJinxel86P600c6JcsHsyNjlqpO7MhjrPO-lcpDGHF9jNZOw"
    days = DAYS_ES
