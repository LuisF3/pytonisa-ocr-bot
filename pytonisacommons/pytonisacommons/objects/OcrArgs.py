from typing import Union, List

class OcrArgs:
    pass

class OcrMyPdfArgs(OcrArgs):
    def __init__(
        self,
        input_file: str = None,
        output_file: str = None,
        language: Union[List[str], None] = None,
        deskew: bool = True,
        rotate_pages: bool = True,
        clean: bool = False,
        clean_final: bool = False,
        remove_background: bool = False,
        optimize: int = 1,
        progress_bar: bool = False,
        **kwargs
    ) -> None:
        self.input_file: str = input_file
        self.output_file: str = output_file
        self.language: List[str] = language
        self.deskew: bool = deskew
        self.rotate_pages: bool = rotate_pages
        self.clean: bool = clean
        self.clean_final: bool = clean_final
        self.remove_background: bool = remove_background
        self.optimize: int = int(optimize)
        self.progress_bar: bool = progress_bar
        
        self.redo_ocr: bool = False
        self.force_ocr: bool = False

    def set_redo_ocr(self):
        self.deskew = False
        self.clean_final = False
        self.remove_background = False
        self.redo_ocr = True

    def set_force_ocr(self):
        self.force_ocr = True