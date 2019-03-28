#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
#  Copyright 2019 The FATE Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
################################################################################
#
#
################################################################################

from arch.api import eggroll
from arch.api.utils import log_utils
from federatedml.feature.hetero_feature_binning.hetero_binning_guest import HeteroFeatureGuest
from federatedml.param import FeatureBinningParam
from federatedml.util import FeatureBinningParamChecker
from federatedml.util import ParamExtract
from federatedml.util import consts
from workflow.workflow import WorkFlow

LOGGER = log_utils.getLogger()


class HeteroBinningGuestWorkflow(WorkFlow):
    def _initialize(self, config_path):
        self._initialize_role_and_mode()
        self._initialize_model(config_path)
        self._initialize_workflow_param(config_path)

    def _initialize_role_and_mode(self):
        self.role = consts.GUEST
        self.mode = consts.HETERO

    def _initialize_intersect(self, config):
        pass

    def _initialize_model(self, runtime_conf_path):
        binning_param = FeatureBinningParam()
        self.binning_param = ParamExtract.parse_param_from_config(binning_param, runtime_conf_path)
        FeatureBinningParamChecker.check_param(self.binning_param)
        self.model = HeteroFeatureGuest(self.binning_param)
        LOGGER.debug("Guest model started")

    def save_binning_result(self):
        # save_dict = {}
        # if self.binning_param.local_only:
        #     save_dict['local'] = []
        #     for idx, iv_attr in enumerate(iv_attrs):
        #         save_dict['local'].append(iv_attr.result_dict)
        #         if self.binning_param.cols != -1:
        #             LOGGER.info("cols {} result: {}".format(self.binning_param.cols[idx],
        #                                                     iv_attr.display_result(
        #                                                         self.binning_param.display_result
        #                                                     )))
        #         else:
        #             LOGGER.info("cols {} result: {}".format(idx,
        #                                                     iv_attr.display_result(
        #                                                         self.binning_param.display_result
        #                                                     )))
        # else:
        #     save_dict['local'] = []
        #     save_dict['remote'] = []
        #     LOGGER.info("Guest Features result:")
        #     for idx, iv_attr in enumerate(iv_attrs['local']):
        #         save_dict['local'].append(iv_attr.result_dict)
        #         if self.binning_param.cols != -1:
        #             LOGGER.info("cols {} result: {}".format(self.binning_param.cols[idx],
        #                                                     iv_attr.display_result(
        #                                                         self.binning_param.display_result
        #                                                     )))
        #         else:
        #             LOGGER.info("cols {} result: {}".format(idx,
        #                                                     iv_attr.display_result(
        #                                                         self.binning_param.display_result
        #                                                     )))
        #
        #     LOGGER.info("Host Features result:")
        #     for idx, iv_attr in enumerate(iv_attrs['remote']):
        #         save_dict['remote'].append(iv_attr.result_dict)
        #         LOGGER.info("remote result, cols {} result: {}".format(idx,
        #                                                                iv_attr.display_result(
        #                                                                    self.binning_param.display_result
        #                                                                )))
        #
        # meta_table = eggroll.parallelize([(1, save_dict)],
        #                                  include_key=True,
        #                                  name=self.binning_param.result_table,
        #                                  namespace=self.binning_param.result_namespace,
        #                                  error_if_exist=False,
        #                                  persistent=True
        #                                  )
        meta_table = self.model.save_model()
        return meta_table

    def run(self):
        self._init_argument()

        if self.workflow_param.method == "binning":

            if self.binning_param.process_method == 'fit':
                train_data_instance = self.gen_data_instance(self.workflow_param.train_input_table,
                                                             self.workflow_param.train_input_namespace,
                                                             mode='fit')
                if self.binning_param.local_only:
                    self.model.fit_local(train_data_instance)
                else:
                    self.model.fit(train_data_instance)
                self.save_binning_result()
            else:
                train_data_instance = self.gen_data_instance(self.workflow_param.train_input_table,
                                                             self.workflow_param.train_input_namespace,
                                                             mode='transform')
                self.load_model()

                if self.binning_param.local_only:
                    self.model.transform_local(train_data_instance)
                else:
                    self.model.transform(train_data_instance)
                self.save_binning_result()
        else:
            raise TypeError("method %s is not support yet" % (self.workflow_param.method))

        LOGGER.info("Task end")


if __name__ == "__main__":
    workflow = HeteroBinningGuestWorkflow()
    workflow.run()
