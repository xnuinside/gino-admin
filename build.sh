cd docs && make html && cd .. && \
poetry build && twine check dist/*