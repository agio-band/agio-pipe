import logging

from agio_pipe.entities.published_file import APublishedFile
from agio_pipe.entities.version import AVersion
from agio_pipe.schemas.version import PublishedFileFull


logger = logging.getLogger(__name__)


def create_product_version(
        product_id: str,
        task_id: str,
        version: int,
        project_files: list[PublishedFileFull],
    ) -> tuple[AVersion, list[dict]]:
        version = AVersion.create(
            product_id=product_id,
            task_id=task_id,
            version=version,
        )
        files = []
        for file in project_files:
            file: PublishedFileFull
            published_file = APublishedFile.create(
                version_id=version.id,
                path=file.publish_path,
            )
            published_file_data = {
                **published_file.to_dict(),
                'orig_path': file.orig_path  # add original path
            }
            files.append(published_file_data)
        return version, files
