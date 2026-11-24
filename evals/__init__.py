import os
import tempfile

os.environ["MONEY_VECTOR_DB"] = tempfile.mkdtemp(prefix="eval_chroma_")