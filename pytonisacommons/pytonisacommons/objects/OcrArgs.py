from typing import Union, List

class OcrArgs:
    def getArgs():
        raise NotImplemented()
    def redo_ocr():
        raise NotImplemented()


class OcrMyPdfArgs(OcrArgs):
    def __init__(
        self,
        input_file: str = None,
        output_file: str = None,
        language: Union[List[str], None] = None,
        redo_ocr: bool = False,
        deskew: bool = True,
        rotate_pages: bool = True,
        clean: bool = False,
        clean_final: bool = False,
        remove_background: bool = False,
        optimize: int = 1,
        progress_bar: bool = False
    ) -> None:
        if language is None:
            language = ['por']

        self.input_file: str = input_file
        self.output_file: str = output_file
        self.language: List[str] = language
        self.redo_ocr: bool = redo_ocr
        self.deskew: bool = deskew
        self.rotate_pages: bool = rotate_pages
        self.clean: bool = clean
        self.clean_final: bool = clean_final
        self.remove_background: bool = remove_background
        self.optimize: int = int(optimize)
        self.progress_bar: bool = progress_bar

    def redo_ocr(self):
        self.deskew = False
        self.clean_final = False
        self.remove_background = False
        self.redo_ocr = True