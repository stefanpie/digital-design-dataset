import argparse
import base64
import io
import re
import shutil
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from socketserver import TCPServer

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import tiktoken
import tqdm
from dotenv import dotenv_values
from joblib import Parallel, delayed
from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.manifold import TSNE

from digital_design_dataset.design_dataset import DesignDataset

current_script_dir = Path(__file__).parent

figure_dir = current_script_dir / "figures"
data_dir = current_script_dir / "output"

env_config = dotenv_values(current_script_dir / ".env")

# load n_jobs
if "N_JOBS" not in env_config:
    raise ValueError("N_JOBS not defined in .env file")
n_jobs_val = env_config["N_JOBS"]
if not n_jobs_val:
    raise ValueError("N_JOBS not defined in .env file")
try:
    n_jobs = int(n_jobs_val)
except ValueError as e:
    raise ValueError("N_JOBS must be an integer") from e
if n_jobs < 1:
    raise ValueError("N_JOBS must be greater than 0")

# load dataset path
if "DB_PATH" in env_config:
    db_path_val = env_config["DB_PATH"]
    if not db_path_val:
        raise ValueError("DB_PATH not defined in .env file")
    try:
        db_path = Path(db_path_val)
    except ValueError as e:
        raise ValueError(
            f"An error occurred while parsing the DB_PATH string into a Path object:\n{e!s}",
        ) from e

dd = DesignDataset(
    db_path,
    overwrite=False,
)


def build_dataset_designs(design_dataset: DesignDataset) -> pd.DataFrame:
    # for each datasource, count the number of designs
    df_dataset_summary = pd.DataFrame(columns=["dataset_name", "design_name"])
    for design in design_dataset.index:
        design_name = design["design_name"]
        dataset_name = design["dataset_name"]
        df_dataset_summary = pd.concat(
            [
                df_dataset_summary,
                pd.DataFrame(
                    {
                        "dataset_name": [dataset_name],
                        "design_name": [design_name],
                    },
                ),
            ],
        )
    return df_dataset_summary


def count_non_whitespace_chars(fp: Path) -> int:
    txt = fp.read_text()
    txt_no_whitespace = "".join(txt.split())
    return len(txt_no_whitespace)


RE_MODULE = re.compile(r"module\s+\S+[\s\S]*?endmodule", re.MULTILINE)


def count_modules(fp: Path) -> int:
    txt = fp.read_text()
    modules = RE_MODULE.findall(txt)
    return len(modules)


def build_dataset_files(design_dataset: DesignDataset) -> pd.DataFrame:
    df_dataset_summary = pd.DataFrame(
        columns=["dataset_name", "design_name", "file_name"],
    )
    for design in design_dataset.index:
        design_name = design["design_name"]
        dataset_name = design["dataset_name"]
        source_files = design_dataset.get_design_source_files(design_name)
        file_name = [fp.name for fp in source_files]
        file_path_relative = [str(fp.relative_to(design_dataset.root_dir)) for fp in source_files]
        df_dataset_summary = pd.concat(
            [
                df_dataset_summary,
                pd.DataFrame(
                    {
                        "dataset_name": [dataset_name] * len(source_files),
                        "design_name": [design_name] * len(source_files),
                        "file_name": file_name,
                        "file_path": file_path_relative,
                    },
                ),
            ],
        )

    return df_dataset_summary


def analyze_design_sources_simple(
    design_dataset: DesignDataset,
    df_dataset_files: pd.DataFrame,
):
    df_source_code_analysis = df_dataset_files.copy()

    print("Counting non-whitespace characters")
    char_counts = Parallel(n_jobs=n_jobs)(
        delayed(count_non_whitespace_chars)(design_dataset.root_dir / x) for x in df_source_code_analysis["file_path"]
    )
    df_source_code_analysis["num_chars"] = char_counts

    print("Counting number of modules")
    module_counts = Parallel(
        n_jobs=n_jobs,
    )(delayed(count_modules)(design_dataset.root_dir / x) for x in df_source_code_analysis["file_path"])
    df_source_code_analysis["num_modules"] = module_counts

    return df_source_code_analysis


TOKENIZERS = {
    "cl100k_base": tiktoken.get_encoding("cl100k_base"),
    "o200k_base": tiktoken.get_encoding("o200k_base"),
}


def count_tokens(fp: Path, tokenizer_name: str) -> int:
    tokenizer = TOKENIZERS[tokenizer_name]
    text = fp.read_text()
    tokens = tokenizer.encode(text)
    num_tokens = len(tokens)
    return num_tokens


def analyze_design_sources_tokenization(
    design_dataset: DesignDataset,
    df_dataset_files: pd.DataFrame,
) -> pd.DataFrame:
    df_tokenizers = []
    for tokenizer_name in TOKENIZERS:
        print(f"Counting tokens - {tokenizer_name}")
        df_tokenizer = df_dataset_files.copy()

        num_tokens = Parallel(n_jobs=n_jobs)(
            delayed(count_tokens)(design_dataset.root_dir / x, tokenizer_name) for x in df_tokenizer["file_path"]
        )
        df_tokenizer["num_tokens"] = num_tokens
        df_tokenizer["tokenizer"] = tokenizer_name
        df_tokenizers.append(df_tokenizer)

    df_tokenizers_combined = pd.concat(df_tokenizers)
    return df_tokenizers_combined


def analyze_design_sources_embedding(
    df_dataset_files: pd.DataFrame,
) -> dict:
    files = df_dataset_files["file_path"].to_list()
    files = [str((dd.root_dir / x).resolve()) for x in files]
    dataset_names = df_dataset_files["dataset_name"].to_list()

    # create vectorizer
    vectorizer = TfidfVectorizer(
        # settings for source code, not english
        input="filename",
        lowercase=False,
        analyzer="char",
        stop_words=None,
        ngram_range=(1, 1),
        max_features=1024,
    )

    # fit vectorizer
    print("Fitting vectorizer")
    X_sparse = vectorizer.fit_transform(tqdm.tqdm(files))
    X_dense = X_sparse.toarray()

    projection_data = {}
    projection_data["dataset_names"] = dataset_names
    projection_data["projections"] = {}

    # PCA
    print("Running PCA")
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_dense)
    projection_data["projections"]["pca"] = X_pca

    # SVD
    print("Running SVD")
    svd = TruncatedSVD(n_components=2)
    X_svd = svd.fit_transform(X_dense)
    projection_data["projections"]["svd"] = X_svd

    # TSNE
    print("Running TSNE")
    tsne = TSNE(n_components=2)
    X_tsne = tsne.fit_transform(X_dense)
    projection_data["projections"]["tsne"] = X_tsne

    return projection_data


def data_uri_from_buffer(buf: io.BytesIO, mime_type: str) -> str:
    data = buf.getvalue()
    data_base64 = base64.b64encode(data)
    data_base64_text = data_base64.decode("utf-8")
    data_uri = f"data:{mime_type};base64,{data_base64_text}"
    return data_uri


def build_rank_plot(
    df: pd.DataFrame,
    data_col: str,
    title: str,
    x_label: str,
    y_label: str,
    log_scale: bool = False,
) -> str:
    df_sorted = df.sort_values(data_col)
    fig, ax = plt.subplots()
    ax.plot(
        range(len(df_sorted)),
        df_sorted[data_col],
        "-x",
        markersize=5,
    )
    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    if log_scale:
        ax.set_yscale("log")
    ax.set_xticks([])

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    fig_uri = data_uri_from_buffer(buf, "image/png")
    return fig_uri


def build_bar_plot(
    df: pd.DataFrame,
    col_cat: str,
    col_data: str,
    title: str,
    label_cat: str,
    label_data: str,
    log_scale: bool = False,
) -> str:
    df_sorted = df.sort_values(col_data)
    fig, ax = plt.subplots()
    sns.barplot(
        x=col_data,
        y=col_cat,
        data=df_sorted,
        ax=ax,
    )
    ax.set_title(title)
    ax.set_xlabel(label_data)
    ax.set_ylabel(label_cat)
    if log_scale:
        ax.set_xscale("log")

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    fig_uri = data_uri_from_buffer(buf, "image/png")
    return fig_uri


def build_histogram_plot(
    df: pd.DataFrame,
    col_data: str,
    title: str,
    x_label: str,
    y_label: str,
    log_scale: tuple[bool, bool] = (False, False),
) -> str:
    fig, ax = plt.subplots()
    sns.histplot(
        df[col_data].to_list(),
        ax=ax,
        log_scale=log_scale,
    )
    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    if log_scale[0]:
        ax.set_xscale("asinh")
    if log_scale[1]:
        ax.set_yscale("asinh")

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    fig_uri = data_uri_from_buffer(buf, "image/png")
    return fig_uri


def build_report(
    df_dataset_summary: pd.DataFrame,
    df_dataset_files: pd.DataFrame,
    report_output_dir: Path,
    df_source_analysis_simple: pd.DataFrame | None = None,
    df_source_analysis_tokenization: pd.DataFrame | None = None,
    source_analysis_embedding_data: dict | None = None,
):
    if report_output_dir.exists():
        shutil.rmtree(report_output_dir)
    report_output_dir.mkdir()

    df_sources = (
        df_dataset_summary.groupby("dataset_name")
        .agg({"design_name": "nunique"})
        .rename(columns={"design_name": "num_designs"})
        .reset_index()
    )
    df_sources = df_sources.sort_values("num_designs", ascending=False)

    html_table_sources = df_sources.to_html(
        index=False,
        columns=["dataset_name", "num_designs"],
        escape=False,
    )

    designs_total = df_sources["num_designs"].sum()

    if df_source_analysis_simple is not None:
        fig_uri_num_chars_hist = build_histogram_plot(
            df_source_analysis_simple,
            "num_chars",
            "Distribution of Number of Non-Whitespace Characters in Source Files",
            "Number of Characters",
            "File Count",
            log_scale=(True, True),
        )

        fig_uri_num_modules_hist = build_histogram_plot(
            df_source_analysis_simple,
            "num_modules",
            "Distribution of Number of Modules in Source Files",
            "Number of Modules",
            "File Count",
            log_scale=(True, True),
        )

        df_source_simple_agg_by_design = (
            df_source_analysis_simple.groupby(
                "design_name",
            )
            .agg(
                {
                    "num_chars": "sum",
                    "num_modules": "sum",
                },
            )
            .reset_index()
        )

        fig_uri_num_chars_hist_by_design = build_histogram_plot(
            df_source_simple_agg_by_design,
            "num_chars",
            "Distribution of Number of Non-Whitespace Characters in Source Files by Design",
            "Number of Characters",
            "Design Count",
            log_scale=(True, True),
        )

        fig_uri_num_modules_hist_by_design = build_histogram_plot(
            df_source_simple_agg_by_design,
            "num_modules",
            "Distribution of Number of Modules in Source Files by Design",
            "Number of Modules",
            "Design Count",
            log_scale=(True, True),
        )

        df_source_simple_agg_by_design_num_chars_sorted = df_source_simple_agg_by_design.sort_values(
            "num_chars",
        )
        fig_uri_num_chars_by_design_ranked = build_rank_plot(
            df_source_simple_agg_by_design_num_chars_sorted,
            "num_chars",
            "Number of Characters per Design",
            "Design Index",
            "Number of Characters",
            log_scale=True,
        )

        df_source_simple_agg_by_design_num_modules_sorted = df_source_simple_agg_by_design.sort_values(
            "num_modules",
        )
        fig_uri_num_modules_by_design_ranked = build_rank_plot(
            df_source_simple_agg_by_design_num_modules_sorted,
            "num_modules",
            "Number of Modules per Design",
            "Design Index",
            "Number of Modules",
            log_scale=True,
        )

        df_source_simple_agg_by_dataset = (
            df_source_analysis_simple.groupby(
                "dataset_name",
            )
            .agg(
                {
                    "num_chars": "sum",
                    "num_modules": "sum",
                },
            )
            .reset_index()
        )

        df_source_simple_agg_by_dataset_num_chars_sorted = df_source_simple_agg_by_dataset.sort_values(
            "num_chars",
        )
        fig_uri_num_chars_by_dataset = build_bar_plot(
            df_source_simple_agg_by_dataset_num_chars_sorted,
            "dataset_name",
            "num_chars",
            "Number of Characters per Dataset",
            "Dataset Name",
            "Number of Characters",
            log_scale=True,
        )

        df_source_simple_agg_by_dataset_num_modules_sorted = df_source_simple_agg_by_dataset.sort_values(
            "num_modules",
        )
        fig_uri_num_modules_by_dataset = build_bar_plot(
            df_source_simple_agg_by_dataset_num_modules_sorted,
            "dataset_name",
            "num_modules",
            "Number of Modules per Dataset",
            "Dataset Name",
            "Number of Modules",
            log_scale=True,
        )

    if df_source_analysis_tokenization is not None:
        tokenizers_unique = df_source_analysis_tokenization["tokenizer"].unique()
        token_plots = {}
        token_counts = {}
        for tokenizer in tokenizers_unique:
            df_sub = df_source_analysis_tokenization[df_source_analysis_tokenization["tokenizer"] == tokenizer]
            total = df_sub["num_tokens"].sum()
            token_counts[tokenizer] = total

            df_agg_by_design = df_sub.groupby("design_name").agg({"num_tokens": "sum"}).reset_index()
            df_agg_by_design_sorted = df_agg_by_design.sort_values("num_tokens")

            fig_uri_num_tokens_by_design_ranked = build_rank_plot(
                df_agg_by_design_sorted,
                "num_tokens",
                f"Number of Tokens per Design - {tokenizer}",
                "Design Index",
                "Number of Tokens",
                log_scale=True,
            )

            df_agg_by_dataset = df_sub.groupby("dataset_name").agg({"num_tokens": "sum"}).reset_index()

            df_agg_by_dataset_sorted = df_agg_by_dataset.sort_values("num_tokens")
            fig_uri_num_tokens_by_dataset = build_bar_plot(
                df_agg_by_dataset_sorted,
                "dataset_name",
                "num_tokens",
                f"Number of Tokens per Dataset - {tokenizer}",
                "Dataset Name",
                "Number of Tokens",
                log_scale=True,
            )

            token_plots[tokenizer] = {
                "fig_uri_num_tokens_by_design_ranked": fig_uri_num_tokens_by_design_ranked,
                "fig_uri_num_tokens_by_dataset": fig_uri_num_tokens_by_dataset,
            }

    if source_analysis_embedding_data is not None:
        figures = {}
        dataset_sources = source_analysis_embedding_data["dataset_names"]

        colors = sns.color_palette("tab10", n_colors=len(dataset_sources))

        projections = source_analysis_embedding_data["projections"]
        for projection_name, projection_data in projections.items():
            fig, ax = plt.subplots(figsize=(8, 8))
            for i, dataset_name in enumerate(dataset_sources):
                x, y = projection_data[i]
                ax.scatter(x, y, label=dataset_name, color=colors[i])
            ax.set_title(f"{projection_name.upper()}: Source Code Embeddings of Designs")
            fig.tight_layout()
            buf = io.BytesIO()
            fig.savefig(buf, format="png")
            fig_uri = data_uri_from_buffer(buf, "image/png")
            figures[projection_name] = fig_uri

    html_report = ""
    html_report += "<html>\n"
    html_report += "<head>\n"
    html_report += "<title>Design Dataset Report</title>\n"
    # styles
    html_report += "<style>\n"
    html_report += "html, body { width: 100%; height: 100%; margin: 0; padding: 0; font-size: 16px; }\n"
    html_report += "* { box-sizing: border-box; }\n"
    html_report += "body { max-width: 80%; margin-left: auto; margin-right: auto; padding-top: 20px; }\n"
    html_report += "table { border-collapse: collapse; width: 100%; }\n"
    html_report += "th, td { border: 1px solid #dddddd; text-align: left; padding: 8px; }\n"
    html_report += "th { background-color: #f2f2f2; }\n"
    html_report += "img { max-width: 100%; }\n"
    html_report += "</style>\n"

    html_report += "</head>\n"
    html_report += "<body>\n"
    html_report += "<h1>Design Dataset Report</h1>\n"
    html_report += "<h2>Dataset Summary</h2>\n"
    html_report += "<div style='border: 1px solid #dddddd; padding: 8px; width: 100%; margin-bottom: 16px;'>\n"
    html_report += (
        f"<p style='margin: 0; font-size: 20px; text-align: center;'><b>Number of Sources: {len(df_sources)}</b></p>\n"
    )
    html_report += (
        f"<p style='margin: 0; font-size: 20px; text-align: center;'><b>Number of Designs: {designs_total}</b></p>\n"
    )
    html_report += "</div>\n"
    html_report += html_table_sources

    if df_source_analysis_simple is not None:
        html_report += "<h2>Source Code Analysis - Simple</h2>\n"
        html_report += "<h3>Summary by File</h3>\n"
        html_report += "<div style='display: grid; grid-template-columns: 1fr 1fr;'>\n"
        html_report += f'<img src="{fig_uri_num_chars_hist}" />\n'
        html_report += f'<img src="{fig_uri_num_modules_hist}" />\n'
        html_report += "</div>\n"
        html_report += "<h3>Summary by Design</h3>\n"
        html_report += "<div style='display: grid; grid-template-columns: 1fr 1fr;'>\n"
        html_report += f'<img src="{fig_uri_num_chars_hist_by_design}" />\n'
        html_report += f'<img src="{fig_uri_num_modules_hist_by_design}" />\n'
        html_report += "</div>\n"
        html_report += "<div style='display: grid; grid-template-columns: 1fr 1fr;'>\n"
        html_report += f'<img src="{fig_uri_num_chars_by_design_ranked}" />\n'
        html_report += f'<img src="{fig_uri_num_modules_by_design_ranked}" />\n'
        html_report += "</div>\n"
        html_report += "<h3>Summary by Dataset</h3>\n"
        html_report += "<div style='display: grid; grid-template-columns: 1fr 1fr;'>\n"
        html_report += f'<img src="{fig_uri_num_chars_by_dataset}" />\n'
        html_report += f'<img src="{fig_uri_num_modules_by_dataset}" />\n'
        html_report += "</div>\n"
    if df_source_analysis_tokenization is not None:
        html_report += "<h2>Source Code Analysis - Tokenization</h2>\n"
        for tokenizer in token_plots:
            html_report += f"<h3>Tokenizer: {tokenizer}</h3>\n"

            html_report += (
                f"<p><b>Total Token Count: {token_counts[tokenizer]:,} aka {token_counts[tokenizer]:.2e}</b></p>\n"
            )
            html_report += "<div style='display: grid; grid-template-columns: 1fr 1fr;'>\n"
            html_report += f'<img src="{token_plots[tokenizer]["fig_uri_num_tokens_by_design_ranked"]}" />\n'
            html_report += f'<img src="{token_plots[tokenizer]["fig_uri_num_tokens_by_dataset"]}" />\n'
            html_report += "</div>\n"

    if source_analysis_embedding_data is not None:
        html_report += "<h2>Source Code Analysis - TD-IDF Embeddings</h2>\n"
        for projection_name, fig_uri in figures.items():
            html_report += f"<h3>{projection_name.upper()} Embeddings</h3>\n"
            html_report += f'<img src="{fig_uri}" />\n'

    html_report += "</body>\n"
    html_report += "</html>\n"

    html_report_fp = report_output_dir / "report.html"
    html_report_fp.write_text(html_report)


class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # Always serve the report.html file
        report_file = Path(self.directory) / "report.html"
        print(self.directory)
        return str(report_file.resolve())

    def do_GET(self):
        self.path = "/report.html"
        return super().do_GET()


class ReportHTTPHandler(CustomHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def do_GET(self):
        self.path = "/report.html"
        return super().do_GET()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a report for a design dataset")
    parser.add_argument("--analyze_basic", action="store_true", default=False, help="Analyze basic metrics")
    parser.add_argument(
        "--analyze_tokenization",
        action="store_true",
        default=False,
        help="Analyze tokenization metrics",
    )
    parser.add_argument(
        "--analyze_embedding",
        action="store_true",
        default=False,
        help="Analyze source code embeddings",
    )
    parser.add_argument(
        "--local_server",
        action="store_true",
        default=False,
        help="Run a local server to view the report",
    )
    parser.add_argument("--port", type=int, default=6000, help="Port to run the local server on")
    parser.add_argument(
        "--report_dir",
        type=Path,
        default=current_script_dir / "report",
        help="Directory to save the report",
    )
    args = parser.parse_args()

    report_dir = args.report_dir

    print("Loading initial tables")
    df_dataset_summary = build_dataset_designs(dd)
    df_dataset_files = build_dataset_files(dd)

    df_source_analysis_simple = None
    df_source_analysis_tokenization = None
    data_source_code_embedding = None

    if args.analyze_basic:
        print("Analyzing design sources - simple")
        df_source_analysis_simple = analyze_design_sources_simple(dd, df_dataset_files)

    if args.analyze_tokenization:
        print("Analyzing design sources - tokenization")
        df_source_analysis_tokenization = analyze_design_sources_tokenization(
            dd,
            df_dataset_files,
        )

    if args.analyze_embedding:
        print("Analyzing design sources - embedding")
        data_source_code_embedding = analyze_design_sources_embedding(df_dataset_files)

    print("Building report")
    build_report(
        df_dataset_summary,
        df_dataset_files,
        report_dir,
        df_source_analysis_simple=df_source_analysis_simple,
        df_source_analysis_tokenization=df_source_analysis_tokenization,
        source_analysis_embedding_data=data_source_code_embedding,
    )

    if args.local_server:
        handler = partial(ReportHTTPHandler, directory=str(report_dir.resolve()))
        with TCPServer(("", args.port), handler) as httpd:
            print(f"Serving at: http://localhost:{args.port}")
            webbrowser.open(f"http://localhost:{args.port}")
            httpd.serve_forever()
    else:
        print(f"Report generated at {report_dir}")
