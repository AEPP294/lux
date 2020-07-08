from lux.vizLib.altair.AltairChart import AltairChart
import altair as alt
alt.data_transformers.disable_max_rows()
class BarChart(AltairChart):
	"""
	BarChart is a subclass of AltairChart that render as a bar charts.
	All rendering properties for bar charts are set here.

	See Also
	--------
	altair-viz.github.io
	"""

	def __init__(self,dobj):
		super().__init__(dobj)
	def __repr__(self):
		return f"Bar Chart <{str(self.view)}>"
	def initialize_chart(self):
		self.tooltip = False
		x_attr = self.view.get_attr_by_channel("x")[0]
		y_attr = self.view.get_attr_by_channel("y")[0]

		self.code += "import altair as alt\n"
		# self.code += f"viewData = pd.DataFrame({str(self.data.to_dict(orient='records'))})\n"
		self.code += f"viewData = pd.DataFrame({str(self.data.to_dict())})\n"

		if (x_attr.data_model == "measure"):
			agg_title = f'{x_attr.aggregation.capitalize()} of {x_attr.attribute}'
			y_attr_field = alt.Y(y_attr.attribute, type= y_attr.data_type, axis=alt.Axis(labelOverlap=True))
			x_attr_field = alt.X(x_attr.attribute, type= x_attr.data_type, title=agg_title)
			y_attr_field_code = f"alt.Y('{y_attr.attribute}', type= '{y_attr.data_type}', axis=alt.Axis(labelOverlap=True))"
			x_attr_field_code = f"alt.X('{x_attr.attribute}', type= '{x_attr.data_type}', title='{agg_title}')"

			if (y_attr.sort=="ascending"):
				y_attr_field.sort="-x"
				y_attr_field_code = f"alt.Y('{y_attr.attribute}', type= '{y_attr.data_type}', axis=alt.Axis(labelOverlap=True), sort ='-x')"
		else:
			agg_title = f"{y_attr.aggregation.capitalize()} of {y_attr.attribute}"
			x_attr_field = alt.X(x_attr.attribute, type = x_attr.data_type,axis=alt.Axis(labelOverlap=True))
			y_attr_field = alt.Y(y_attr.attribute,type=y_attr.data_type,title=agg_title)
			x_attr_field_code = f"alt.X('{x_attr.attribute}', type= '{x_attr.data_type}', axis=alt.Axis(labelOverlap=True))"
			y_attr_field_code = f"alt.Y('{y_attr.attribute}', type= '{y_attr.data_type}', title='{agg_title}')"
			if (x_attr.sort=="ascending"):
				x_attr_field.sort="-y"
				x_attr_field_code = f"alt.X('{x_attr.attribute}', type= '{x_attr.data_type}', axis=alt.Axis(labelOverlap=True),sort='-y')"
			
		chart = alt.Chart(self.data).mark_bar().encode(
			    y = y_attr_field,
			    x = x_attr_field
			)
		# TODO: tooltip messes up the count() bar charts		
		# Can not do interactive whenever you have default count measure otherwise output strange error (Javascript Error: Cannot read property 'length' of undefined)
		#chart = chart.interactive() # If you want to enable Zooming and Panning
		chart = chart.configure_mark(tooltip=alt.TooltipContent('encoding')) # Setting tooltip as non-null

		self.code += f'''
		chart = alt.Chart(viewData).mark_bar(size=12).encode(
		    y = {y_attr_field_code},
		    x = {x_attr_field_code},
		)
		chart = chart.configure_mark(tooltip=alt.TooltipContent('encoding')) # Setting tooltip as non-null
		'''
		return chart 