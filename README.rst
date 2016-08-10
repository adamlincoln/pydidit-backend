pydidit-backend
==========================

pydidit is a todo system flexible enough to fit your style.

This package is the backend for pydidit.


Authors
-------

Adam J. Lincoln <adamjlincoln@gmail.com>

Claudio Bryla <claudiobryla@gmail.com>


Install
-------

cp pyditit.sample-ini ~/.pydiditrc
cp alembic.sample-ini alembic.ini

Modify sqlalchemy.url in both .pydiditrc and alembic.ini 

alembic upgrade head

You did it!

Credits
-------

- `Distribute`_
- `Buildout`_
- `modern-package-template`_

.. _Buildout: http://www.buildout.org/
.. _Distribute: http://pypi.python.org/pypi/distribute
.. _`modern-package-template`: http://pypi.python.org/pypi/modern-package-template
