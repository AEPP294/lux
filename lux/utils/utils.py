def convert2List(x):
	'''
	"a" --> ["a"]
	["a","b"] --> ["a","b"]
	'''
	if type(x) != list:
		return [x]
	else:
		return x

def pandasToLux(df):
	from lux.luxDataFrame.LuxDataframe import LuxDataFrame
	values = df.values.tolist()
	ldf = LuxDataFrame(values, columns = df.columns)
	return(ldf)

def getAttrsSpecs(specLst):
	specObj = list(filter(lambda x: x.value=="", specLst))
	return specObj

def getFilterSpecs(specLst):
	specObj = list(filter(lambda x: x.value!="", specLst))
	return specObj

def checkImportLuxWidget():
	import pkgutil
	if (pkgutil.find_loader("luxWidget") is None):
		raise Exception("luxWidget is not installed. Run `npm i lux-widget' to install the Jupyter widget.\nSee more at: https://github.com/lux-org/lux-widget")


