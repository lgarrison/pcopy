import concurrent.futures
import shutil
from pathlib import Path
from typing import TypeAlias
from os import PathLike

import typer
from typing_extensions import Annotated

# TODO: separate the Typer entry point from the library function so we can use types like this?
StrPath: TypeAlias = str | PathLike[str]


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
    sources: Annotated[
        list[Path],
        typer.Argument(metavar='SRC...', help='Source files or directories'),
    ],
    dest: Annotated[Path, typer.Argument(help='Destination file or directory')],
    workers: Annotated[
        int, typer.Option('--workers', '-w', help='Number of parallel workers')
    ] = 16,
    sendfile: Annotated[
        bool,
        typer.Option(
            '--sendfile', '-s', help='Whether to use the sendfile syscall for copies'
        ),
    ] = False,
):
    if isinstance(sources, (str, PathLike)):
        sources = [sources]
    sources = [Path(src) for src in sources]

    # Warning: if using pcopy as a library, note the global state
    shutil._USE_CP_SENDFILE = sendfile

    dest_dir_exists = dest.is_dir()

    # With multiple sources, dest must be a directory
    if len(sources) > 1 and not dest_dir_exists:
        raise typer.BadParameter(
            'Destination must be a directory when copying multiple sources'
        )

    with MultithreadedCopier(max_workers=workers) as copier:
        for src in sources:
            # Behave like `cp -r src dest` if dest exists
            dst = dest / src.name if dest_dir_exists else dest

            # This probably does one more stat than we need
            if dst.exists() and src.samefile(dst):
                raise typer.BadParameter(f'src and dest are the same: {src} -> {dst}')

            if src.is_file():
                copier.copy(src, dst)
            else:
                if src in dst.parents:
                    raise typer.BadParameter(
                        f'Cannot copy a directory into itself: {src} -> {dst}'
                    )
                shutil.copytree(src, dst, copy_function=copier.copy, dirs_exist_ok=True)


def main():
    typer.run(pcopy)


if __name__ == '__main__':
    main()
