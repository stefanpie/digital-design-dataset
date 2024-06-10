import re
import string
from pathlib import Path

# sklearn.feature_extraction.text.CountVectorizer
from sklearn.feature_extraction.text import CountVectorizer

from digital_design_dataset.design_dataset import DesignDataset

current_script_dir = Path(__file__).parent

output_dir = current_script_dir / "output"

test_db_dir = current_script_dir / "test_dataset_v2"
test_dataset = DesignDataset(test_db_dir)

corpus_fps = []
design_names = []
dataset_names = []
for design in test_dataset.index:
    source_files = test_dataset.get_design_source_files(design["design_name"])
    for fp in source_files:
        corpus_fps.append(fp)
        design_names.append(design["design_name"])
        dataset_names.append(design["dataset_name"])

vocab = {c: i for i, c in enumerate(list(string.printable))}
vocab_size = len(vocab)
print(f"Vocab size: {vocab_size}")

vectorizer = CountVectorizer(
    input="filename",
    analyzer="char",
    lowercase=False,
    vocabulary=vocab,
)

X = vectorizer.transform(corpus_fps)
print(X.shape)

RE_C_COMMENT = re.compile(
    r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
    re.DOTALL | re.MULTILINE,
)


def comment_replacer(match):
    s = match.group(0)
    if s.startswith("/"):
        return " "  # note: a space and not an empty string
    return s


def comment_remover(text):
    return re.sub(RE_C_COMMENT, comment_replacer, text)


RE_MODULE = re.compile(r"module[ \t]*([^\s]*)[ \t]*(?:\(|#)(?:.*|\s)*?endmodule")


def hash_modules_from_file(fp: Path, design_name: str, dataset_name: str):
    source = fp.read_text()
    source_no_comments = comment_remover(source)

    data = []

    module_matches = re.finditer(RE_MODULE, source_no_comments)
    for m in module_matches:
        module_name = m.group(1)
        module_text = m.group(0)
        module_text_no_whitespace = re.sub(r"\s+", "", module_text)

    return data
