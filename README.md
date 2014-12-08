# libfritter

[![Build Status](https://travis-ci.org/PeterJCLaw/libfritter.svg)](https://travis-ci.org/PeterJCLaw/libfritter)

Libfritter contains the core email sending components of [Student Robotics'](https://www.studentrobotics.org)
user management and user mailing software. In both cases it operates on
email templates stored as plaintext files.

It is not generally useful on its own, other than the `preview` script
which allows individual templates to be previewed, optionally restricting
the preview to use a collection of valid placeholders.

## Requirements
The tests are run via `nosetests`, so you'll need `python-nose` for them.
The docs are build via [Sphinx](http://sphinx-doc.org/) with the `numpydoc`
extension for saner parameter documentation.

## About

The history of this prior to the addition of this README is a git
filter-branch extraction from the nemesis repo.
