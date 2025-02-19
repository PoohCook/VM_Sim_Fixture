
MAKE = make
.PHONY: test update libs
BUILD_IMAGE = ./SB4TestFrameworkPackage
PACKAGE = ./SB4TestFrameworkPackage.zip

clean:
	rm -f *.o *.so
	rm -rf extout
	rm -rf tmp

lint:
	pycodestyle scripts --config=.pycodestyle.cfg
	pygount ./scripts | awk '$$1 > 100'

package:
	rm -rf $(BUILD_IMAGE)
	mkdir $(BUILD_IMAGE)
	rm -rf ./scripts/__pycache__
	cp ./scripts/* $(BUILD_IMAGE)
	find $(BUILD_IMAGE) -type f -name "*.py" -exec gsed -i '/env python3/d' {} +
	cp  ./Debug/SB4-StmTestFixture.bin $(BUILD_IMAGE)
	zip -r $(PACKAGE) $(BUILD_IMAGE)
	rm -rf $(BUILD_IMAGE)
