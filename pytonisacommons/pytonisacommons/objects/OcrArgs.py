from builtins import NotImplementedError
from typing import List
import argparse

class OcrArgs:
    def get_args(self):
        raise NotImplementedError()

class OcrMyPdfArgs(OcrArgs):
    def __init__(
        self,
        language: List[str] = None,
        deskew: bool = True,
        rotate_pages: bool = True,
        clean: bool = False,
        clean_final: bool = False,
        remove_background: bool = False,
        optimize: int = 1,
        progress_bar: bool = False,
        arg_string: str = None,
        **kwargs
    ) -> None:
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

        if not arg_string is None:
            self.process_arg_string(arg_string)

    def set_redo_ocr(self):
        self.deskew = False
        self.clean_final = False
        self.remove_background = False
        self.redo_ocr = True

    def set_force_ocr(self):
        self.force_ocr = True

    def process_arg_string(self, arg_string: str) -> None:
        parser: argparse.ArgumentParser = argparse.ArgumentParser(description='Configuration of the ocr processing')
        parser.add_argument('-l', nargs='*', default=['por'], help='Languages to be identified, space separated') #TODO if user uses "-l " the language becomes empty

        args_str = filter(None, arg_string.split(' '))
        args = parser.parse_args(args_str)
        
        self.language = args.l

    def get_args(self):
        return self.__dict__.copy()