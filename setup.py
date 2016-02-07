#!/usr/bin/env python
import io
import os
import subprocess
import tarfile
import shutil
import sysconfig
from setuptools import setup
from distutils.extension import Extension
from distutils.command.build_ext import build_ext


DEPENDENCY_VERSIONS = {
    "onig": "5.9.6",
    "jq": "1.5"
}

long_description = io.open('README.rst', encoding='utf-8').read()


def path_in_dir(relative_path):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), relative_path))


class jq_build_ext(build_ext):
    def run(self):
        # self._build_oniguruma()
        # self._build_libjq()
        build_ext.run(self)

    def _build_oniguruma(self):
        self._safe_rmtree("dependencies/onig_install")
        self._safe_rmtree("dependencies/onig-{onig}".format(**DEPENDENCY_VERSIONS))

        self._extract_tarball("dependencies/onig-{onig}.tar.gz".format(**DEPENDENCY_VERSIONS))
        self._build_lib(
            lib_dir="dependencies/onig-{onig}".format(**DEPENDENCY_VERSIONS),
            commands=[
                ["./configure", "CFLAGS=-fPIC", "--prefix=%s/dependencies/onig_install" % (os.getcwd())],
                ["make"],
                ["make", "install"],
            ]
        )

    def _build_libjq(self):
        self._safe_rmtree("dependencies/jq-jq-{jq}".format(**DEPENDENCY_VERSIONS))

        self._extract_tarball("dependencies/jq-{jq}.tar.gz".format(**DEPENDENCY_VERSIONS))
        self._build_lib(
            lib_dir="dependencies/jq-jq-{jq}".format(**DEPENDENCY_VERSIONS),
            commands=[
                ["autoreconf", "-i"],
                ["./configure", "CFLAGS=-fPIC", "--disable-maintainer-mode", "--with-oniguruma=%s/dependencies/onig_install" % (os.getcwd())],
                ["make", "-j8", "LDFLAGS=-all-static"],
            ]
        )

    def _build_lib(self, lib_dir, commands):
        macosx_deployment_target = sysconfig.get_config_var("MACOSX_DEPLOYMENT_TARGET")
        if macosx_deployment_target:
            os.environ['MACOSX_DEPLOYMENT_TARGET'] = macosx_deployment_target

        def run_command(args):
            print("Executing: %s" % ' '.join(args))
            subprocess.check_call(args, cwd=lib_dir)

        for command in commands:
            run_command(command)

    def _extract_tarball(self, tarball_path):
        tarfile.open(tarball_path, "r:gz").extractall(path_in_dir("./dependencies"))

    def _safe_rmtree(self, d):
        try:
            shutil.rmtree(d)
        except OSError:
            pass


pyjq = Extension(
    "_pyjq",
    sources=[
        "_pyjq.c"
    ],
    include_dirs=[
        "dependencies/jq-jq-{jq}".format(**DEPENDENCY_VERSIONS)
    ],
    extra_objects=[
        "dependencies/jq-jq-{jq}/.libs/libjq.a".format(**DEPENDENCY_VERSIONS),
        "dependencies/onig-{onig}/.libs/libonig.a".format(**DEPENDENCY_VERSIONS)
    ],
)

setup(
    py_modules=['pyjq'],
    install_requires=['six'],
    test_suite='test_pyjq',
    ext_modules=[pyjq],
    cmdclass={
        "build_ext": jq_build_ext,
    },
    name='pyjq',
    version='1.1',
    description='Binding for jq JSON processor.',
    long_description=long_description,
    author='OMOTO Kenji',
    url='http://github.com/doloopwhile/pyjq',
    license='MIT License',
    package_data={
        '': [
            'dependencies/jq-{jq}.tar.gz'.format(**DEPENDENCY_VERSIONS),
            'dependencies/onig-{onig}.tar.gz'.format(**DEPENDENCY_VERSIONS)
        ]
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: JavaScript',
    ],
)
