from torchvision.transforms import ToTensor

from server import PromptServer
import os
import re
import random
from PIL import Image

def pil_to_tens(image):
    if image.mode == 'RGBA':
      image = image.convert('RGB')
    return ToTensor()(image).unsqueeze(0).permute(0, 2, 3, 1)

class ImageFromDirSelector:
    def __init__(self) -> None:
        self.current_image = None
        self.current_tensor = None

    CATEGORY = 'Nich/utils'
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)

    FUNCTION = "sample_images"

    OUTPUT_IS_LIST = (False,)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "directory": ("STRING", { "default": "~/images" }),
                "keep_current_selection": ("BOOLEAN", { "default": False }),
                "selected_image_name": ("STRING", { "multiline": True, "dynamicPrompts": False })
            },
            "optional": {
                "regexp_filter": ("STRING", { "default": None, "multiline": True })
            },
            "hidden": {"unique_id": "UNIQUE_ID"}
        }

    @classmethod
    def IS_CHANGED(cls, directory, unique_id, keep_current_selection, selected_image_filename=None, regexp_filter=None):
        return "" if keep_current_selection else selected_image_filename

    def get_current_image(self, selected_image_name):
        return selected_image_name if selected_image_name else self.current_image

    def requires_new_image(self, current_image, keep_current_selection):
        return not current_image or not keep_current_selection

    def get_files(self, full_path, regexp_filter):
        files = os.listdir(full_path)
        if regexp_filter:
            reg = re.compile(regexp_filter)
            files = [file for file in files if re.search(reg, file)]
        return files

    def sample_images(self, directory, unique_id, keep_current_selection=False, selected_image_name=None, regexp_filter=None):
        full_path = os.path.expanduser(directory)
        prior_selected_image = self.get_current_image(selected_image_name)
        new_image = prior_selected_image
        new_image_required = self.requires_new_image(prior_selected_image, keep_current_selection)
        if new_image_required:
            files = self.get_files(full_path, regexp_filter)
            image_files = [file for file in files if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
            self.current_image = random.choice(image_files)
            new_image = self.current_image

        PromptServer.instance.send_sync("nich-image-selected", {"node_id": unique_id, "value": new_image})

        if new_image_required or self.current_tensor is None:
            image = Image.open(os.path.join(full_path, new_image))
            self.current_tensor = pil_to_tens(image).unsqueeze(0)

        return self.current_tensor

NODE_CLASS_MAPPINGS = {
    "Image from Dir Selector (Nich)": ImageFromDirSelector
}

