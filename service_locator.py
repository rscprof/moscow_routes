class Service_locator:

    instance = None

    def __init__(self):
        self.services = {}

    def register_service(self, name: str, service):
        self.services[name] = service

    def get_service(self, name: str):
        return self.services[name]

    @classmethod
    def get_instance(cls):
        if cls.instance is None:
            cls.instance = cls()
        return cls.instance
