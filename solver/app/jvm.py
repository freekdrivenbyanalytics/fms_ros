import os

import jdk4py

_started = False


def ensure_jvm_env() -> None:
    """Point JPype at the bundled jdk4py JDK before any timefold import.

    Must run before `import timefold...` anywhere in the process. The JDK's
    own bin/ directory must be on PATH or native library loading fails with
    "Can't find dependent libraries" even though the JDK is functional.
    """
    global _started
    if _started:
        return
    os.environ["JAVA_HOME"] = str(jdk4py.JAVA_HOME)
    os.environ["PATH"] = str(jdk4py.JAVA_HOME / "bin") + os.pathsep + os.environ.get("PATH", "")
    _started = True
