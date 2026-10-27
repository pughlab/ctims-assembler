"""
This module models the config json file. The structure should look like this
{
  "filters": {
    "maf": {
      "Variant_Classification": [...]
    }
  }
}

The structure generally follows these rules
1. On the outermost layer is the config type. In this case, only 'filters' is needed.
2. Within the filters property will be the datasets that require filtering
3. Within the dataset property, the column(s) that require filtering and the blacklist of values


"""

from dataclasses import dataclass
from typing import List


@dataclass
class MAF:
    Variant_Classification: List[str]


@dataclass
class Filter:
    maf: MAF

@dataclass
class Config:
    filters: Filter
