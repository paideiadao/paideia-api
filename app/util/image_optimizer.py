import re
from PIL import Image
from io import BytesIO

class ImageOptimizer:
    def __init__(self):
        self.name = "pillow_image_optimizer"

    def compress(self, file_bytes: BytesIO, resolution: int):
        image = Image.open(file_bytes)
        image.thumbnail((resolution, resolution))
        raw_bytes = BytesIO()
        # test channels
        format = "JPEG"
        if image.mode == "RGBA":
            format = "PNG"
        image.save(raw_bytes, format=format)
        raw_bytes.seek(0)
        return raw_bytes

    @staticmethod
    def get_size(size, resolution):
        h, w = size
        mn, mx = min(h, w), max(h, w)
        cf = resolution / mx
        mx = int(mx * cf)
        mn = int(mn * cf)
        if h > w:
            return (mx, mn)
        return (mn, mx)


pillow_image_optimizer = ImageOptimizer()
