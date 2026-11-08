from importlib.metadata import version, PackageNotFoundError
from .transcriber import Transcriber

try:
    __version__ = version("eng-to-ru-transcriber")
except PackageNotFoundError:
    __version__ = "0.0.0-dev"

__all__ = ["Transcriber"]
