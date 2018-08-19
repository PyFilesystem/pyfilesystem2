from .base import patch_method, NotPatched, Patch


class PatchBuiltins(Patch):
    def get_module(self):
        module = globals()["__builtins__"]
        return module

    @patch_method()
    def open(
        self,
        file,
        mode="r",
        buffering=-1,
        encoding=None,
        errors=None,
        newline=None,
        closefd=True,
        opener=None,
    ):
        try:
            return self.fs.open(
                file,
                mode=mode,
                buffering=buffering,
                encoding=encoding,
                errors=errors,
                newline=newline,
            )
        except NotPatched:
            return original(open)(
                file,
                mode=mode,
                buffering=buffering,
                encoding=encoding,
                errors=errors,
                newline=newline,
                closefd=closefd,
                opener=opener,
            )
