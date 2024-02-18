import urllib.request
from PIL import Image, ImageEnhance
from pathlib import Path
import numpy as np
from typing import Union


class ImageHandler:
    DOWNLOAD_LOCATION = r'/home/pi/repos/ex-machina-wall/raspberry-pi-controller/raspberry_pi_controller/image_handling/downloads'  
    SAVE_LOCATION = r'/home/pi/repos/ex-machina-wall/raspberry-pi-controller/raspberry_pi_controller/image_handling/images'  
    
    def __init__(self):
        pass
    
    def get_num_frames(self, name: str) -> int:
        img = Image.open(Path(self.SAVE_LOCATION, name))
        return img.n_frames

    def _open_saved_image(self, path: Path, resize: tuple = (17, 13), frame: int = None) -> np.array:
        img = Image.open(path)
        if img.is_animated:
            img.seek(frame)
        converter = ImageEnhance.Color(img)
        img = converter.enhance(4)
        img = img.resize(resize)
        img.save(Path(path.parent, f"{path.stem}_small.png"), "PNG")
        
        # Convert the resized image to a NumPy array
        image_array = np.array(img)
        return image_array

    def get_image_from_url(self, url: str) -> np.array:
        download_path = Path(self.DOWNLOAD_LOCATION, "downloaded_image.png")
        urllib.request.urlretrieve(url, download_path)
        return self._open_saved_image(download_path)
        
    
    def open_saved_image(self, name: str, frame: int = None) -> np.array:
        return self._open_saved_image(Path(self.SAVE_LOCATION, name), frame=frame)

