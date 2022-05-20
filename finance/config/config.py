"""This module generates the config by reading and parsing the config files.
See tests for more examples.
"""
from __future__ import annotations
import os
from os.path import join
from copy import deepcopy
import logging
from typing import Union

import pandas as pd

import finance
from finance import ROOT_DIR
from finance.utils.file import read_json


logger = logging.getLogger(__loader__.name)


class IsNonOverridableError(Exception):
    pass


class NewKeyError(Exception):
    pass


class OverridingError(Exception):
    pass


__config = None


def get_cache_config(cache_name: str) -> Dict[str, str]:
    """Returns the path to the requests cache."""

    config = get_config()
    cache_config = config["cache"][cache_name]

    if not os.path.isabs(cache_config["path"]):
        cache_config["path"] = os.path.normpath(os.path.join(finance.ROOT_DIR, cache_config["path"]))
    
    if "expire_after" in cache_config and cache_config["expire_after"]:
        cache_config["expire_after"] = pd.Timedelta(cache_config["expire_after"]).to_pytimedelta()
    else:
        cache_config["expire_after"] = None

    return cache_config


def get_credentials() -> dict:
    """Retrieve the credentials from the path specified in the credentials file."""

    config = get_config()
    credentials_path = config["credentials_path"]

    if not os.path.isabs(credentials_path):
        credentials_path = os.path.normpath(os.path.join(finance.ROOT_DIR, credentials_path))

    credentials = read_json(path=credentials_path)

    return credentials


def get_config() -> dict:
    """This function retrieves the global object detection engine for this module.

    This function ensures that the engine is created only when it is needed.
    If the engine has not yet been created it is created.

    Returns:
        __config: An object that can be used to create run object detection
    """

    if __config is None:
        return read_base_config()
    else:
        return __config


def initialise_config(*configs: Union[str, dict]) -> None:
    """This function initialises a package wide configuration object.

    Parameters:
        configs: The paths to the configuration files that will be
            merged with the base config. Can also be passed directly as
            dictionaries.
    """

    global __config

    if __config is None:
        logger.info("Creating package config.")
        __config = generate_config(*configs)
    else:
        raise ValueError("The config has already been initialised. It cannot be initialised twice.")


def read_base_config() -> dict:
    """Load the base configuration."""
    return read_json(join(ROOT_DIR, "config", "base_config.json"))


def generate_config(*configs: Union[str, dict]) -> dict:
    """Generate the configuration dictionary.

    This function uses the base configuration and merges it
    with any another configuration files that are needed to
    override the defaults.

    Parameters:
        *configs (str or dict): Zero or more paths to json files that contain
            configuration to override the base_dictionary. The order
            of the files matters since the overrides are applied sequentially.
            It's also possible to pass a dictionaries, in which case the dictionaries
            be passed directly.

    Returns:
        merged_config (dict): A dictionary of configuration. Can be used to instantiate
            a Pype object.
    """

    configs = [read_json(config) if isinstance(config, str) else config for config in configs]

    return generate_config_from_dictionaries(*configs)


def generate_config_from_dictionaries(*configs: dict) -> dict:
    """See generate_config documentation.

    Instead of using file paths, this function uses dictionaries.
    """
    base_config = read_base_config()
    is_non_overridable = read_json(join(ROOT_DIR, "config", "is_non_overridable.json"))

    try:
        merged_config = merge_overridable_dictionaries(base_config, *configs, is_non_overridable=is_non_overridable)
    except (NewKeyError, OverridingError) as e:
        raise type(e)(f"Error when merging config files.") from e

    return merged_config


def merge_overridable_dictionaries(
    base_dictionary: dict,
    *dictionaries: dict,
    is_non_overridable: dict = None,
    raise_new_keys: bool = True,
    raise_overriding: bool = False,
) -> dict:
    """Merge multiple dictionaries into a single one if fields are overridable.

    This function takes a base_dictionary (dict) and one or more dictionaries (dict) and
    returns a single dictionary. The dictionaries must be given in order of priority.
    If the dictionaries contain fields that are not in the base_dictionary, these fields
    will be ignored.

    Parameters:
        base_dictionarys (dict): The base_dictionary. This defines all the fields
            and default values of the dictionary to output.
        *dictionaries (dict): One or more dictionary files to override the base_dictionary.
        is_non_overridable (dict): A dictionary that specifies fields for the base_dictionary
            that are not overridable. The values of this dictionary at are the keys of the
            base_dictionary that are not overridable.
        add_keys (bool): Whether or not to create keys if not present in the base. Defaults to False.
        raise_new_keys (bool): Whether to raise if there are keys in the dictionary
            that are not in the base_dictionary.
    """

    merged_dictionary = deepcopy(base_dictionary)

    for dictionary in dictionaries:

        if is_non_overridable is not None:
            is_non_overridable_validation(is_non_overridable)
            overriding_dictionary_validation(dictionary, is_non_overridable)
            overriding_base_dictionary_validation(merged_dictionary, is_non_overridable)

        merged_dictionary = merge_dictionaries(
            merged_dictionary, dictionary, raise_new_keys=raise_new_keys, raise_overriding=raise_overriding
        )

    return merged_dictionary


def merge_dictionaries(
    base_dictionary: dict, dictionary: dict, raise_overriding: bool = False, raise_new_keys: bool = False
) -> dict:
    """Recursive dictionary merge.

    Instead of updating only top-level keys, dictionary_merge recurses down
    into nested dictionaries to an arbitrary depth, updating keys. The dictionary parameter
    is merged into base_dictionary.

    This version will return a copy of the dictionary and leave the original
    arguments untouched.

    The optional argument add_keys, determines whether keys which are
    present in dictionary but not base_dictionary should be included in the
    new dictionary.

    Parameters:
        base_dictionary (dict): Dictionary into which the merge is made.
        dictionary (dict): Dictionary to merge into base_dictionary.
        add_keys (bool): Whether to add new keys. Defaults to False.
        raise_new_keys (bool): Whether to raise if there are keys in the dictionary
            that are not in the base_dictionary.

    Returns:
        merged_dictionary: Result of merging the dictionary.

    Raises:
        NewKeyError: When a new key is being added to the dictionary
            and raise_new_keys is set to True
        OverridingError: When a key in the base dictionary is being overriden
            and raise_overriding is set to True.
    """
    merged_dictionary = deepcopy(base_dictionary)

    for key in dictionary.keys():

        if key in base_dictionary and isinstance(base_dictionary[key], dict) and isinstance(dictionary[key], dict):

            merged_dictionary[key] = merge_dictionaries(
                base_dictionary[key], dictionary[key], raise_overriding=raise_overriding, raise_new_keys=raise_new_keys
            )
        else:
            if key in base_dictionary and raise_overriding:
                raise OverridingError(f"Cannot override keys when raise_overriding is True. Trying to override {key}")
            elif key not in base_dictionary and raise_new_keys:
                raise NewKeyError(f"Cannot add new key when raise_new_keys is True. New key is {key}")
            else:
                merged_dictionary[key] = dictionary[key]

    return merged_dictionary


def is_non_overridable_validation(is_non_overridable: dict) -> None:
    """Validation function for the is_non_overridable dictionary.

    This function validates the format of the dictionary that is
    used to indicate whether elements of the base dictionary are
    not overridable.
    A is_non_overridable dictionary is considered to be valid
    if all its values that are not dictionaries are of value True.
    This function raises an exception if the dictionary is not valid
    and returns None if it is.

    Parameters:
       is_non_overridable (dict): Indicates if an element of the
       base config dictionary is not overridable.

    Returns:
        Raises an exception if the dictionary is not valid.
        None if the dictionary is valid.

    Examples:
        is_non_overridable = {
            'b': {
                'b1': True,
                'b5' : True,
                'b7': {
                    'b8': False
                }
            }
        }
        is a valid example.

        is_non_overridable = {
            'b': {
                'b1': True,
                'b5' : [1, 2],
                'b7': {
                    'b8': False
                }
            }
        }
        is not a valid example (because of the list and False).
    """

    for key, value in is_non_overridable.items():

        if not isinstance(key, str):
            raise IsNonOverridableError(
                "All keys of the is_non_overridable " f"dictionary must be strings. Found: {key} of type: {type(key)} "
            )

        if isinstance(value, dict):
            return is_non_overridable_validation(is_non_overridable[key])
        else:
            if value != True:
                raise IsNonOverridableError(
                    "All values of the is_non_overridable " f"dictionary must be True. Found: {value}"
                )


def overriding_dictionary_validation(dictionary: dict, is_non_overridable: dict) -> None:
    """Validate the config dictionary based on the is_non_overridable.

    This function validates that the dictionary that is used to override the
    base dictionary does not contain any values that are specified as non overridable
    by the is_non_overridable dictionary.
    An exception will be raised if an error is found.

    Parameters:
        dictionary (dict): Dictionary to validate.
        is_non_overridable (dict): Indicates if an element of the base dictionary
            is non overridable. Must conform to the format specificied in
            is_non_overridable_validation.

    Returns:
        Raises an exception if the dictionary contains a field that is marked as
        non overridable in is_non_overridable.
        None if the dictionary is valid.
    """

    intersection = set(dictionary).intersection(set(is_non_overridable))

    for key in intersection:

        if is_non_overridable[key] == True:
            raise IsNonOverridableError(f"Dictionary attempting to override a non overridable field: {key}.")

        elif isinstance(is_non_overridable[key], dict) and isinstance(dictionary[key], dict):
            overriding_dictionary_validation(dictionary[key], is_non_overridable[key])

        else:
            raise IsNonOverridableError("Dictionary and non overridable are not compatible")


def overriding_base_dictionary_validation(base_dictionary: dict, is_non_overridable: dict) -> None:
    """Validate the base dictionary based on the is_non_overridable.

    This function validates that is_non_overridable dictionary does not contain keys that are
    not present in the base dictionary.
    An exception will be raised if an error is found.

    Parameters:
        base_dictionary (dict): Base dictionary.
        is_non_overridable (dict): Indicates if an element of the base dictionary
            is non overridable. Must conform to the format specificied in
            is_non_overridable_validation.

    Returns:
        Raises an exception if the is_non_overridable dictionary contains a value
            that is not present in base_dictionary.
        non overridable in is_non_overridable.
        None if the dictionary is valid.
    """

    difference = set(is_non_overridable) - set(base_dictionary)

    if len(difference) != 0:
        raise IsNonOverridableError("The is_non_overridable contains fields " "that are not in the base_dictionary.")

    intersection = set(is_non_overridable).intersection(set(base_dictionary))

    for key in intersection:
        if isinstance(is_non_overridable[key], dict) and isinstance(base_dictionary[key], dict):
            overriding_base_dictionary_validation(base_dictionary[key], is_non_overridable[key])
