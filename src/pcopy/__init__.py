import concurrent.futures
import shutil
from pathlib import Path

import typer
from typing_extensions import Annotated


class MultithreadedCopier(concurrent.futures.ThreadPoolExecutor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._futures = []

    def copy(self, source, dest):
        fut = self.submit(shutil.copy2, source, dest)
        self._futures.append(fut)

    def __exit__(self, *args):
        # Wait for all futures to complete
        super().__exit__(*args)

        # Raise any exceptions
        for future in self._futures:
            future.result()


def pcopy(
    src_dir: list[Path],
    dest_dir: Path,
    workers: Annotated[
        int, typer.Option("--workers", "-w", help="Number of parallel workers")
    ] = 16,
    sendfile: Annotated[
        bool,
        typer.Option(
            "--sendfile", "-s", help="Whether to use the sendfile syscall for copies"
        ),
    ] = False,
):
    if isinstance(src_dir, (str, Path)):
        src_dir = [src_dir]
    src_dir = [Path(src) for src in src_dir]

    # Warning: if using pcopy as a library, note the global state
    shutil._USE_CP_SENDFILE = sendfile

    dest_dir_exists = dest_dir.is_dir()
    with MultithreadedCopier(max_workers=workers) as copier:
        for src in src_dir:
            # Behave like `cp -r src dest` if dest exists
            dst = dest_dir / src.name if dest_dir_exists else dest_dir
            shutil.copytree(src, dst, copy_function=copier.copy, dirs_exist_ok=True)


def main():
    typer.run(pcopy)


if __name__ == "__main__":
    main()
