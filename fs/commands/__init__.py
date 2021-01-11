#!/usr/bin/env python

from .fs2   import fs2
from .help  import help
from .ls    import ls
from .cat   import cat
from .mkdir import mkdir
from .tree  import tree
from .cp    import cp
from .mv    import mv
from .rm    import rm
from .dl    import dl
from .up    import up

fs2.add_command(help )
fs2.add_command(ls   )
fs2.add_command(cat  )
fs2.add_command(mkdir)
fs2.add_command(tree )
fs2.add_command(cp   )
fs2.add_command(mv   )
fs2.add_command(rm   )
fs2.add_command(dl   )
fs2.add_command(up   )

__all__ = ["fs2"]
