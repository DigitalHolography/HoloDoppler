"""Discover code packages and map the canonical presets into built distributions."""
from setuptools import find_namespace_packages, setup


setup(packages=[*find_namespace_packages(include=["holodoppler*"]), "holodoppler.parameters"])
