from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from pathlib import Path


@dataclass(frozen=True)
class HandicPaths:
    package: str = "handic"
    dicdir_name: str = "dicdir"
    version_filename: str = "version"

    def dicdir(self) -> Path:
        """
        Return the absolute path to the bundled dictionary directory:
        site-packages/handic/dicdir
        """
        # resources.files works for normal installs and many zip/wheel layouts.
        base = resources.files(self.package)
        d = base / self.dicdir_name

        # Convert Traversable -> real filesystem path if possible
        try:
            path = Path(d)
        except TypeError:
            # In rare cases (e.g., zipped), we would need as_file().
            # For MeCab, we need a real directory path, so extract to a temp dir.
            # This is unusual for wheels; kept for completeness.
            with resources.as_file(d) as extracted:
                path = Path(extracted)

        if not path.exists():
            raise FileNotFoundError(
                f"HanDic directory not found: {path}\n"
                f"Please ensure the package includes '{self.dicdir_name}' directory."
            )
        return path
    
    def version_file(self) -> Path:
        """
        Return path to HanDic version file: dicdir/version
        """
        vpath = self.dicdir() / self.version_filename
        if not vpath.exists():
            raise FileNotFoundError(f"HanDic version file not found: {vpath}")
        return vpath

    def version(self) -> str:
        """
        Read and return HanDic version string.
        """
        return self.version_file().read_text(encoding="utf-8").strip()


PATHS = HandicPaths()
