from setuptools import setup, find_packages

setup(
    name = "z3c.conditionalviews",
    version = "1.0b",
    author = "Michael Kerrin",
    author_email = "michael.kerrin@openapp.ie",
    url = "http://svn.zope.org/z3c.conditionalviews/",
    description = "Validation mechanism for conditional HTTP requests.",
    long_description = (
        open("README.txt").read() +
        "\n\n" +
        open("CHANGES.txt").read()),
    license = "ZPL 2.1",

    packages = find_packages("src"),
    package_dir = {"": "src"},
    namespace_packages = ["z3c"],
    install_requires = ["setuptools",
                        "zope.component",
                        "zope.schema"],
    extras_require = dict(test = ["zope.app.testing",
                                  "zope.app.zcmlfiles",
                                  "zope.app.securitypolicy",
                                  ]),

    include_package_data = True,
    zip_safe = False,
    )
