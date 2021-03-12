sed '/## Changelog/q' README.md > new_README.md
cat CHANGELOG.txt >> new_README.md
rm README.md
mv new_README.md README.md
rm -r dist
cd docs && make html && cd .. && \
poetry build && twine check dist/*