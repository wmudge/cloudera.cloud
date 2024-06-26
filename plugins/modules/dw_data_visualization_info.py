#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2023 Cloudera, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cloudera.cloud.plugins.module_utils.cdp_common import CdpModule

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = r"""
---
module: dw_data_visualization_info
short_description: Gather information about CDP Data Visualization Instances
description:
    - Gather information about CDP Data Visualization Instances
author:
  - "Webster Mudge (@wmudge)"
  - "Dan Chaffelson (@chaffelson)"
  - "Ronald Suplina (@rsuplina)"
requirements:
  - cdpy
options:
  cluster_id:
    description:
      - The identifier of the Data Warehouse Cluster.
      - Mutually exclusive with I(environment).
    type: str
  environment:
    description:
      - The name or CRN of the Environment in which to find and describe Data Visualization Instances
      - Mutually exclusive with I(cluster_id).
    type: str
    aliases:
      - env
  data_visualization_id:
    description:
      - The ID of Data Visualization Instance
      - Mutually exclusive with I(data_visualization_name).
    type: str
    aliases:
      - id
    required: False
  data_visualization_name:
    description:
      - The name of Data Visualization Instance
      - Mutually exclusive with I(data_visualization_id).
    type: str
    aliases:
      - name
    required: False
extends_documentation_fragment:
  - cloudera.cloud.cdp_sdk_options
  - cloudera.cloud.cdp_auth_options
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details.

# Gather information about Data Visualization Instances within an CDW Environment
- cloudera.cloud.dw_data_visualization_info:
    env: example-environment

# Gather information about Data Visualization Instances within an CDW Environment
- cloudera.cloud.dw_data_visualization_info:
    cluster_id: env-xyzabc

# Gather information about specific Data Visualization Instance within an CDW Environment
- cloudera.cloud.dw_data_visualization_info:
    cluster_id: env-xyzabc
    data_visualization_name: example-name

"""

RETURN = r"""
---
clusters:
  description: The information about the named Data Visualization Instance or Instances
  returned: always
  type: list
  elements: dict
  contains:
    creatorCrn:
      description: The CRN of the creator of the Data Visualization Instance
      returned: always
      type: str
    id:
      description: The unique id of the Data Visualization instance
      returned: always
      type: str
    imageVersion:
      description: The current version of Data Visualization
      returned: always
      type: str
    name:
      description: The name of the Data Visualization instance
      returned: always
      type: str
    size:
      description: The size of the Data Visualization instance
      returned: always
      type: str
    status:
      description: The status of the Data Visualization instance
      returned: always
      type: str
sdk_out:
  description: Returns the captured CDP SDK log.
  returned: when supported
  type: str
sdk_out_lines:
  description: Returns a list of each line of the captured CDP SDK log.
  returned: when supported
  type: list
  elements: str
"""


class DwDataVisualizationInfo(CdpModule):
    def __init__(self, module):
        super(DwDataVisualizationInfo, self).__init__(module)

        # Set variables
        self.data_visualization_id = self._get_param("data_visualization_id")
        self.data_visualization_name = self._get_param("data_visualization_name")
        self.cluster_id = self._get_param("cluster_id")
        self.environment = self._get_param("environment")

        self.clusters = []

        # Initialize return values
        self.data_visualizations = []

    @CdpModule._Decorators.process_debug
    def process(self):
        if self.cluster_id is not None:
            cluster_single = self.cdpy.dw.describe_cluster(self.cluster_id)
            if cluster_single is not None:
                self.clusters.append(cluster_single)
        elif self.environment is not None:
            env_crn = self.cdpy.environments.resolve_environment_crn(self.environment)
            if env_crn:
                self.clusters = self.cdpy.dw.list_clusters(env_crn=env_crn)
        if not self.clusters:
            self.module.fail_json(
                msg="No clusters found for the specified filter. Cluster ID: {}, Env ID: {}".format(
                    self.cluster_id, self.environment
                )
            )

        for cluster in self.clusters:
            resp = self.cdpy.dw.list_data_visualizations(cluster_id=cluster["id"])
            self.data_visualizations.extend(
                [
                    v
                    for v in resp
                    if (
                        self.data_visualization_id is None
                        or v["id"] == self.data_visualization_id
                    )
                    and (
                        self.data_visualization_name is None
                        or v["name"] == self.data_visualization_name
                    )
                ]
            )


def main():
    module = AnsibleModule(
        argument_spec=CdpModule.argument_spec(
            data_visualization_id=dict(type="str", aliases=["id"]),
            data_visualization_name=dict(type="str", aliases=["name"]),
            cluster_id=dict(type="str"),
            environment=dict(type="str", aliases=["env"]),
        ),
        mutually_exclusive=[
            ["cluster_id", "environment"],
            ["data_visualization_id", "data_visualization_name"],
        ],
        supports_check_mode=True,
    )

    instance = DwDataVisualizationInfo(module)
    instance.process()
    output = dict(changed=False, data_visualizations=instance.data_visualizations)

    if instance.debug:
        output.update(sdk_out=instance.log_out, sdk_out_lines=instance.log_lines)

    module.exit_json(**output)


if __name__ == "__main__":
    main()
