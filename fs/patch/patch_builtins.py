from .base import patch_method, NotPatched, Patch


class PatchBuiltins(Patch):
    def get_module(self):
        import builtins
        return builtins

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
                self.from_cwd(file),
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
