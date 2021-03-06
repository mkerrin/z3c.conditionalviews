from setuptools import setup, find_packages

setup(
    name = "z3c.conditionalviews",
    version = "1.1dev",
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
                        "zope.app.http",
                        "zope.schema",
                        "zope.app.publication",
                        ],

    extras_require = dict(
        test = ["zope.securitypolicy",
                "zope.app.wsgi",
                ]),

    include_package_data = True,
    zip_safe = False,
    )
