from setuptools import setup, find_packages

setup(
    name = "z3c.conditionalviews",
    version = "1.0",
    author = "Michael Kerrin",
    author_email = "zope3-users@zope.org",
    url = "http://svn.zope.org/z3c.conditionalviews/",
    description = open("README.txt").read(),
    long_description = (
        open("src/z3c/conditionalviews/README.txt").read() +
        "\n\n" +
        open("CHANGES.txt").read()),
    license = "ZPL 2.1",
    classifiers = ["Environment :: Web Environment",
                   "Intended Audience :: Developers",
                   "License :: OSI Approved :: Zope Public License",
                   "Programming Language :: Python",
                   "Framework :: Zope3",
                   ],

    packages = find_packages("src"),
    package_dir = {"": "src"},
    namespace_packages = ["z3c"],
    install_requires = ["setuptools",
                        "zope.component",
                        "zope.schema"],
    extras_require = dict(test = ["zope.app.testing",
                                  "zope.app.zcmlfiles",
                                  "zope.securitypolicy",
                                  ]),

    include_package_data = True,
    zip_safe = False,
    )
