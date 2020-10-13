'''
This config file was largely borrowed from Pandas config.py set_action functionality.
For more resources, see https://github.com/pandas-dev/pandas/blob/master/pandas/_config
'''
from collections import namedtuple
from typing import Any, Callable, Dict, Iterable, List, Optional

RegisteredOption = namedtuple("RegisteredOption", "name action display_condition args")

# holds registered option metadata
_registered_actions: Dict[str, RegisteredOption] = {}
update_actions: Dict[str, bool] = {}
update_actions["flag"] = False

def _get_action(pat: str, silent: bool = False):
	return _registered_actions[pat]

class DictWrapper:
	def __init__(self, d: Dict[str, Any], prefix: str = ""):
		object.__setattr__(self, "d", d)
		object.__setattr__(self, "prefix", prefix)
	def __init__(self, d: Dict[str, RegisteredOption], prefix: str = ""):
		object.__setattr__(self, "d", d)
		object.__setattr__(self, "prefix", prefix)

	def __getattr__(self, name: str):
		"""
    	Gets a specific registered action by id
    	Parameters
    	----------
    	`name` - the id for the actions
    	Return
    	-------
    	DictWrapper object for the action
    	"""
		prefix = object.__getattribute__(self, "prefix")
		if prefix:
			prefix += "."
		prefix += name
		try:
			v = object.__getattribute__(self, "d")[name]
		except KeyError as err:
			raise OptionError("No such option") from err
		if isinstance(v, dict):
			return DictWrapper(v, prefix)
		else:
			return _get_action(prefix)

	def __getactions__(self):
		"""
    	Gathers all currently registered actions in a list of DictWrapper
    	Return
    	-------
    	a list of DictWrapper objects that are registered
    	"""
		l = []
		for name in self.__dir__():
			l.append(self.__getattr__(name))
		return l

	def __len__(self):
		return len(list(self.d.keys()))

	def __dir__(self) -> Iterable[str]:
		return list(self.d.keys())

actions = DictWrapper(_registered_actions)


def register_action(
	name: str = "",
    action: Callable[[Any], Any] = None,
    display_condition: Optional[Callable[[Any], Any]] = None,
    *args,
) -> None:
	"""
    Parameters
    ----------
    `name` - the id for the actions
    `action` - the function to be applied to the dataframe
    `display_condition` - the function to check whether or not the function should be applied
    `args` - any additional arguments the function may require
    Description
    -------
    Registers the provided action globally in lux
    """
	name = name.lower()
	if action:
		is_callable(action)

	if display_condition:
		is_callable(display_condition)
	_registered_actions[name] = RegisteredOption(
		name=name, action=action, display_condition=display_condition, args=args
	)
	update_actions["flag"] = True

def remove_action(
	name: str = "",
) -> None:
	"""
    Parameters
    ----------
    `name` - the id for the action to remove
    Description
    -------
    Removes the provided action globally in lux
    """
	name = name.lower()
	if name not in _registered_actions:
		raise ValueError(f"Option '{name}' has not been registered")

	del _registered_actions[name]
	update_actions["flag"] = True

def is_callable(obj) -> bool:
	"""
    Parameters
    ----------
    `obj` - the object to be checked
    Returns
    -------
    validator - returns True if object is callable
        raises ValueError otherwise.
    """
	if not callable(obj):
		raise ValueError("Value must be a callable")
	return True
	