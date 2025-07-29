from typing import Optional

from agio.core.settings.package_settings import APackageSettings


class PipeLocalSettings(APackageSettings):
    publish_temp_dir: Optional[str] = None
