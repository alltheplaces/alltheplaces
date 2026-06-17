from locations.spiders.mitsubishi_cl import MitsubishiCLSpider


class MitsubishiBOSpider(MitsubishiCLSpider):
    name = "mitsubishi_bo"
    start_urls = ["https://mitsubishi-motors.bo/red"]
