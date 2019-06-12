#to run this locally do:
#make pre-python-installs
#.....these exports below
#export DYLD_LIBRARY_PATH=$VIRTUAL_ENV/lib/python2.7/site-packages/PySide
#export PYTHONPATH="src"
#python src/bin/lumber_mill.py

create-env:
	echo "foo"
	virtualenv ~/.basepipe

pre-python-installs:
	#https://github.com/pyside/PySide/issues/129
	brew install cmake && \
	brew tap cartr/qt4 && \
	brew install qt@4 && \
	brew install sip qt@4
	which qmake
	ls -la /usr/local/bin/qmake

build-app:
	rm -rf ./dist
	export DYLD_LIBRARY_PATH=$$VIRTUAL_ENV/lib/python2.7/site-packages/PySide && \
	export PYTHONPATH="./src" && \
		python setup.py py2app -A
		cp ./src/shotgun_api3/lib/httplib2/cacerts.txt ./dist/lumber_mill.app/Contents/MacOS/

install:
	pip install pip -U && \
	pip install -r requirements.txt

install-cli:
	pip install pip -U && \
	pip install -r requirements-cli.txt

test:
	export DYLD_LIBRARY_PATH=$$VIRTUAL_ENV/lib/python2.7/site-packages/PySide && \
		echo "pass for now"

lint:
	pylint --disable=R,C,W \
		--disable=no-name-in-module \
		--disable=import-error --disable=no-member --ignore=shotgun_api3 src

lint-cli:
	pylint --disable=R,C syncs3

all: pre-python-installs install lint test
