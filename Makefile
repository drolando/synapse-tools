DATE := $(shell date +'%Y-%m-%d')
SYNAPSETOOLSVERSION := $(shell sed 's/.*(\(.*\)).*/\1/;q' src/debian/changelog)
bintray.json: bintray.json.in src/debian/changelog
	sed -e 's/@DATE@/$(DATE)/g' -e 's/@SYNAPSETOOLSVERSION@/$(SYNAPSETOOLSVERSION)/g' $< > $@

itest_%: package_%
	rm -rf dockerfiles/itest/itest_$*
	cp -a dockerfiles/itest/itest dockerfiles/itest/itest_$*
	cp dockerfiles/itest/itest/Dockerfile.$* dockerfiles/itest/itest_$*/Dockerfile
	tox -e itest_$*

package_%:
	[ -d dist ] || mkdir dist
	tox -e package_$*

clean:
	tox -e fix_permissions
	git clean -Xfd
