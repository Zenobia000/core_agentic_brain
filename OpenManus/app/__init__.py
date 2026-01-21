# Python version check: 3.11-3.13
import sys
import warnings
import os

# Suppress PyTorch warnings through environment variables (must be set early)
os.environ["PYTORCH_ALLOC_CONF"] = "expandable_segments:True"

# Suppress all deprecation warnings at app level
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*TripleDES.*")
warnings.filterwarnings("ignore", message=".*underscore_attrs_are_private.*")


if sys.version_info < (3, 11) or sys.version_info > (3, 13):
    print(
        "Warning: Unsupported Python version {ver}, please use 3.11-3.13".format(
            ver=".".join(map(str, sys.version_info))
        )
    )
