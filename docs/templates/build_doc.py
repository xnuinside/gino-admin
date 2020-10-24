import os
# import shutil
from typing import Text

from m2r import parse_from_file

current_path = os.path.dirname(os.path.abspath(__file__))
docs_path = os.path.dirname(current_path)


def build_readme_rst_from_md():
    readme_rst_path = os.path.join(docs_path, "README.rst")
    readme_md_path = os.path.join(os.path.dirname(docs_path), "README.md")
    readme = parse_from_file(readme_md_path)
    readme = readme.replace("~~", "--").replace("docs/img/", "img/")
    with open(readme_rst_path, "w+") as target_file:
        target_file.write(readme)
    return readme


def build_index(readme: Text):
    index = os.path.join(current_path, "index.template")
    index_rst = os.path.join(docs_path, "source", "index.rst")
    readme = readme.replace("img/", "../img/")
    with open(index, "r") as in_template:
        index = in_template.read()
        index = index.format(readme=readme)
        with open(index_rst, "w+") as target_file:
            target_file.write(index)


def replace_version_in_docs(version: Text) -> None:
    # todo: need to fix it
    file_names = ["quick_start.rst"]
    for name in file_names:
        file_path = os.path.join(docs_path, "source", name)
        with open(file_path, "r") as target_file:
            content = target_file.read()
            content = content.format(version=version)
        with open(file_path, "w+") as target_file:
            target_file.write(content)


def get_version(readme: Text) -> Text:
    version = readme.split("pip install gino-admin==")[1].split()[0]
    print(version, "version")
    return version


def remove_old_img_links():
    pass


def move_rst_to_source():
    pass


def main():
    readme = build_readme_rst_from_md()
    build_index(readme)
    # version = get_version(readme)
    # replace_version_in_docs(version)
    remove_old_img_links()
    move_rst_to_source()
    print("Docs was updated")


if __name__ == "__main__":
    main()
