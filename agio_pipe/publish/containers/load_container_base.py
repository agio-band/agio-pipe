

class LoadContainerBase(ABC):
    @classmethod
    def create(cls, product_version: AProductVersion):
        raise NotImplementedError()

    def execute(self, **kwargs):
        raise NotImplementedError()

    def validate(self):
        raise NotImplementedError()
