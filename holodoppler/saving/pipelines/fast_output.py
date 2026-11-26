"""Output organization for the fast pipeline."""

from holodoppler.core.progress import check_cancelled
from holodoppler.saving.default_output import DefaultOutput


class FastOutput(DefaultOutput):
    """Export the fast pipeline's complete buffers and preview images."""

    def __init__(self, reader, config, *, preview=False):
        super().__init__(reader, config.as_dict(),
                         custom_relative_path="preview" if preview else None)
        self.preview = preview

    def write_buffers(self, buffers, count, progress_callback=None):
        for index in range(count):
            check_cancelled(progress_callback)
            if self.preview:
                for name, images in buffers.items():
                    self.write_static(name, images[index])
            else:
                self.add_batch({name: images[index] for name, images in buffers.items()}, index)
