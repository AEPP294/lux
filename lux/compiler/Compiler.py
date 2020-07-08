from lux.context import Spec
from typing import List, Dict, Union
from lux.view.View import View
from lux.luxDataFrame.LuxDataframe import LuxDataFrame
from lux.view.ViewCollection import ViewCollection
from lux.utils import date_utils
import pandas as pd
import numpy as np


class Compiler:
	'''
	Given a context with underspecified inputs, compile the context into fully specified views for visualization.
	'''

	def __init__(self):
		self.name = "Compiler"

	def __repr__(self):
		return f"<Compiler>"

	@staticmethod
	def compile(ldf: LuxDataFrame,spec_lst:List[Spec], view_collection: ViewCollection, enumerate_collection=True) -> ViewCollection:
		"""
		Compiles input specifications in the context of the ldf into a collection of lux.View objects for visualization.
		1) Enumerate a collection of views interested by the user to generate a view collection
		2) Expand underspecified specifications(lux.Spec) for each of the generated views.
		3) Determine encoding properties for each view

		Parameters
		----------
		ldf : lux.luxDataFrame.LuxDataFrame
			LuxDataFrame with underspecified context.
		view_collection : list[lux.view.View]
			empty list that will be populated with specified lux.View objects.
		enumerate_collection : boolean
			A boolean value that signals when to generate a collection of visualizations.

		Returns
		-------
		view_collection: list[lux.View]
			view collection with compiled lux.View objects.
		"""
		if (enumerate_collection):
			view_collection = Compiler.enumerate_collection(spec_lst,ldf)
		view_collection = Compiler.expandUnderspecified(ldf, view_collection)  # autofill data type/model information
		if len(view_collection)>1: 
			view_collection = Compiler.removeAllInvalid(view_collection) # remove invalid views from collection
		for view in view_collection:
			Compiler.determineEncoding(ldf, view)  # autofill viz related information
		return view_collection

	@staticmethod
	def enumerate_collection(spec_lst:List[Spec],ldf: LuxDataFrame) -> ViewCollection:
		"""
		Given specifications that have been expanded thorught populateOptions,
		recursively iterate over the resulting list combinations to generate a View collection.

		Parameters
		----------
		ldf : lux.luxDataFrame.LuxDataFrame
			LuxDataFrame with underspecified context.

		Returns
		-------
		ViewCollection: list[lux.View]
			view collection with compiled lux.View objects.
		"""
		import copy
		specs = Compiler.populateWildcardOptions(spec_lst,ldf)
		attributes = specs['attributes']
		filters = specs['filters']
		if len(attributes) == 0 and len(filters) > 0:
			ldf.filter_specs = filters
			return []

		collection = []

		# TODO: generate combinations of column attributes recursively by continuing to accumulate attributes for len(colAtrr) times
		def combine(colAttrs, accum):
			last = (len(colAttrs) == 1)
			n = len(colAttrs[0])
			for i in range(n):
				columnList = copy.deepcopy(accum + [colAttrs[0][i]])
				if last:
					if len(filters) > 0:  # if we have filters, generate combinations for each row.
						for row in filters:
							spec_lst = copy.deepcopy(columnList + [row])
							view = View(spec_lst, title=f"{row.attribute} {row.filter_op} {row.value}")
							collection.append(view)
					else:
						view = View(columnList)
						collection.append(view)
				else:
					combine(colAttrs[1:], columnList)
		combine(attributes, [])
		return ViewCollection(collection)

	@staticmethod
	def expandUnderspecified(ldf, view_collection):
		"""
		Given a underspecified Spec, populate the data_type and data_model information accordingly

		Parameters
		----------
		ldf : lux.luxDataFrame.LuxDataFrame
			LuxDataFrame with underspecified context

		view_collection : list[lux.view.View]
			List of lux.View objects that will have their underspecified Spec details filled out.
		Returns
		-------
		views: list[lux.View]
			view collection with compiled lux.View objects.
		"""		
		# TODO: copy might not be neccesary
		import copy
		views = copy.deepcopy(view_collection)  # Preserve the original dobj
		for view in views:
			for spec in view.spec_lst:
				if spec.description == "?":
					spec.description = ""
				if spec.attribute:
					if (spec.data_type == ""):
						spec.data_type = ldf.data_type_lookup[spec.attribute]
					if (spec.data_model == ""):
						spec.data_model = ldf.data_model_lookup[spec.attribute]
				if (spec.value!=""):
					if(isinstance(spec.value,np.datetime64)):
						# TODO: Make this more general and not specific to Year attributes
						chart_title = date_utils.date_formatter(spec.value,ldf)
					else:
						chart_title = spec.value
					view.title = f"{spec.attribute} {spec.filter_op} {chart_title}"
		return views

	@staticmethod
	def removeAllInvalid(view_collection:ViewCollection) -> ViewCollection:
		"""
		Given an expanded view collection, remove all views that are invalid.
		Currently, the invalid views are ones that contain two of the same attribute, no more than two temporal attributes, or overlapping attributes (same filter attribute and visualized attribute).
		Parameters
		----------
		view_collection : list[lux.view.View]
			empty list that will be populated with specified lux.View objects.
		Returns
		-------
		views: list[lux.View]
			view collection with compiled lux.View objects.
		"""
		newVC = []
		for view in view_collection:
			numTemporalSpecs = 0
			attributeSet = set()
			for spec in view.spec_lst:
				attributeSet.add(spec.attribute)
				if spec.data_type == "temporal":
					numTemporalSpecs += 1
			allDistinctSpecs = 0 == len(view.spec_lst) - len(attributeSet)
			if numTemporalSpecs < 2 and allDistinctSpecs:
				newVC.append(view)

		return ViewCollection(newVC)

	@staticmethod
	def determineEncoding(ldf: LuxDataFrame,view: View):
		'''
		Populates View with the appropriate mark type and channel information based on ShowMe logic
		Currently support up to 3 dimensions or measures
		
		Parameters
		----------
		ldf : lux.luxDataFrame.LuxDataFrame
			LuxDataFrame with underspecified context
		view : lux.view.View

		Returns
		-------
		None

		Notes
		-----
		Implementing automatic encoding from Tableau's VizQL
		Mackinlay, J. D., Hanrahan, P., & Stolte, C. (2007).
		Show Me: Automatic presentation for visual analysis.
		IEEE Transactions on Visualization and Computer Graphics, 13(6), 1137–1144.
		https://doi.org/10.1109/TVCG.2007.70594
		'''
		# Count number of measures and dimensions
		Ndim = 0
		Nmsr = 0
		filters = []
		for spec in view.spec_lst:
			if (spec.value==""):
				if (spec.data_model == "dimension"):
					Ndim += 1
				elif (spec.data_model == "measure" and spec.attribute!="Record"):
					Nmsr += 1
			else:  # preserve to add back to spec_lst later
				filters.append(spec)
		# Helper function (TODO: Move this into utils)
		def lineOrBar(ldf,dimension, measure):
			dimType = dimension.data_type
			# If no aggregation function is specified, then default as average
			if (measure.aggregation==""):
				measure.aggregation = "mean"
			if (dimType == "temporal" or dimType == "oridinal"):
				return "line", {"x": dimension, "y": measure}
			else:  # unordered categorical
				# if cardinality large than 5 then sort bars
				if ldf.cardinality[dimension.attribute]>5:
					dimension.sort = "ascending"
				return "bar", {"x": measure, "y": dimension}
		

		# ShowMe logic + additional heuristics
		#countCol = Spec( attribute="count()", data_model="measure")
		countCol = Spec( attribute="Record", aggregation="count", data_model="measure", data_type="quantitative")
		# x_attr = view.get_attr_by_channel("x") # not used as of now
		# y_attr = view.get_attr_by_channel("y")
		# zAttr = view.get_attr_by_channel("z")
		autoChannel={}
		if (Ndim == 0 and Nmsr == 1):
			# Histogram with Count 
			measure = view.get_attr_by_data_model("measure",exclude_record=True)[0]
			if (len(view.get_attr_by_attr_name("Record"))<0):
				view.spec_lst.append(countCol)
			# If no bin specified, then default as 10
			if (measure.bin_size == 0):
				measure.bin_size = 10
			autoChannel = {"x": measure, "y": countCol}
			view.x_min_max = ldf.x_min_max
			view.mark = "histogram"
		elif (Ndim == 1 and (Nmsr == 0 or Nmsr == 1)):
			# Line or Bar Chart
			if (Nmsr == 0):
				view.spec_lst.append(countCol)
			dimension = view.get_attr_by_data_model("dimension")[0]
			measure = view.get_attr_by_data_model("measure")[0]
			view.mark, autoChannel = lineOrBar(ldf,dimension, measure) 
		elif (Ndim == 2 and (Nmsr == 0 or Nmsr == 1)):
			# Line or Bar chart broken down by the dimension
			dimensions = view.get_attr_by_data_model("dimension")
			d1 = dimensions[0]
			d2 = dimensions[1]
			if (ldf.cardinality[d1.attribute] < ldf.cardinality[d2.attribute]):
				# d1.channel = "color"
				view.remove_column_from_spec(d1.attribute)
				dimension = d2
				color_attr = d1
			else:
				if (d1.attribute == d2.attribute):
					view.spec_lst.pop(
						0)  # if same attribute then remove_column_from_spec will remove both dims, we only want to remove one
				else:
					view.remove_column_from_spec(d2.attribute)
				dimension = d1
				color_attr = d2
			# Colored Bar/Line chart with Count as default measure
			if (Nmsr == 0):
				view.spec_lst.append(countCol)
			measure = view.get_attr_by_data_model("measure")[0]
			view.mark, autoChannel = lineOrBar(ldf,dimension, measure)
			autoChannel["color"] = color_attr
		elif (Ndim == 0 and Nmsr == 2):
			# Scatterplot
			view.x_min_max = ldf.x_min_max
			view.y_min_max = ldf.y_min_max
			view.mark = "scatter"
			autoChannel = {"x": view.spec_lst[0],
						   "y": view.spec_lst[1]}
		elif (Ndim == 1 and Nmsr == 2):
			# Scatterplot broken down by the dimension
			measure = view.get_attr_by_data_model("measure")
			m1 = measure[0]
			m2 = measure[1]

			color_attr = view.get_attr_by_data_model("dimension")[0]
			view.remove_column_from_spec(color_attr)
			view.x_min_max = ldf.x_min_max
			view.y_min_max = ldf.y_min_max
			view.mark = "scatter"
			autoChannel = {"x": m1,
						   "y": m2,
						   "color": color_attr}
		elif (Ndim == 0 and Nmsr == 3):
			# Scatterplot with color
			view.x_min_max = ldf.x_min_max
			view.y_min_max = ldf.y_min_max
			view.mark = "scatter"
			autoChannel = {"x": view.spec_lst[0],
						   "y": view.spec_lst[1],
						   "color": view.spec_lst[2]}
		if (autoChannel!={}):
			view = Compiler.enforceSpecifiedChannel(view, autoChannel)
			view.spec_lst.extend(filters)  # add back the preserved filters

	@staticmethod
	def enforceSpecifiedChannel(view: View, autoChannel: Dict[str,str]):
		"""
		Enforces that the channels specified in the View by users overrides the showMe autoChannels.
		
		Parameters
		----------
		view : lux.view.View
			Input View without channel specification.
		autoChannel : Dict[str,str]
			Key-value pair in the form [channel: attributeName] specifying the showMe recommended channel location.
		
		Returns
		-------
		view : lux.view.View
			View with channel specification combining both original and autoChannel specification.
		
		Raises
		------
		ValueError
			Ensures no more than one attribute is placed in the same channel.
		"""		
		resultDict = {}  # result of enforcing specified channel will be stored in resultDict
		specifiedDict = {}  # specifiedDict={"x":[],"y":[list of Dobj with y specified as channel]}
		# create a dictionary of specified channels in the given dobj
		for val in autoChannel.keys():
			specifiedDict[val] = view.get_attr_by_channel(val)
			resultDict[val] = ""
		# for every element, replace with what's in specifiedDict if specified
		for sVal, sAttr in specifiedDict.items():
			if (len(sAttr) == 1):  # if specified in dobj
				# remove the specified channel from autoChannel (matching by value, since channel key may not be same)
				for i in list(autoChannel.keys()):
					if ((autoChannel[i].attribute == sAttr[0].attribute)
						and (autoChannel[i].channel==sVal)): # need to ensure that the channel is the same (edge case when duplicate Cols with same attribute name)
						autoChannel.pop(i)
						break
				sAttr[0].channel = sVal
				resultDict[sVal] = sAttr[0]
			elif (len(sAttr) > 1):
				raise ValueError("There should not be more than one attribute specified in the same channel.")
		# For the leftover channels that are still unspecified in resultDict,
		# and the leftovers in the autoChannel specification,
		# step through them together and fill it automatically.
		leftover_channels = list(filter(lambda x: resultDict[x] == '', resultDict))
		for leftover_channel, leftover_encoding in zip(leftover_channels, autoChannel.values()):
			leftover_encoding.channel = leftover_channel
			resultDict[leftover_channel] = leftover_encoding
		view.spec_lst = list(resultDict.values())
		return view

	@staticmethod
	# def populateWildcardOptions(ldf: LuxDataFrame) -> dict:
	def populateWildcardOptions(spec_lst:List[Spec],ldf: LuxDataFrame) -> dict:
		"""
		Given wildcards and constraints in the LuxDataFrame's context,
		return the list of available values that satisfies the data_type or data_model constraints.

		Parameters
		----------
		ldf : LuxDataFrame
			LuxDataFrame with row or attributes populated with available wildcard options.

		Returns
		-------
		specs: Dict[str,list]
			a dictionary that holds the attributes and filters generated from wildcards and constraints.
		"""
		import copy
		from lux.utils.utils import convert_to_list

		specs = {"attributes": [], "filters": []}
		for spec in spec_lst:
			specOptions = []
			if spec.value == "":  # attribute
				if spec.attribute == "?":
					options = set(list(ldf.columns))  # all attributes
					if (spec.data_type != ""):
						options = options.intersection(set(ldf.data_type[spec.data_type]))
					if (spec.data_model != ""):
						options = options.intersection(set(ldf.data_model[spec.data_model]))
					options = list(options)
				else:
					options = convert_to_list(spec.attribute)
				for optStr in options:
					if str(optStr) not in spec.exclude:
						specCopy = copy.copy(spec)
						specCopy.attribute = optStr
						specOptions.append(specCopy)
				specs["attributes"].append(specOptions)
			else:  # filters
				attrLst = convert_to_list(spec.attribute)
				for attr in attrLst:
					options = []
					if spec.value == "?":
						options = ldf.unique_values[attr]
						specInd = spec_lst.index(spec)
						spec_lst[specInd] = Spec(attribute=spec.attribute, filter_op="=", value=list(options))
					else:
						options.extend(convert_to_list(spec.value))
					for optStr in options:
						if str(optStr) not in spec.exclude:
							specCopy = copy.copy(spec)
							specCopy.attribute = attr
							specCopy.value = optStr
							specOptions.append(specCopy)
				specs["filters"].extend(specOptions)

		return specs
