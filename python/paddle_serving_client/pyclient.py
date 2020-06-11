# Copyright (c) 2020 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# pylint: disable=doc-string-missing
import grpc
from .proto import general_python_service_pb2
from .proto import general_python_service_pb2_grpc
import numpy as np


class PyClient(object):
    def __init__(self):
        self._channel = None

    def connect(self, endpoint):
        self._channel = grpc.insecure_channel(endpoint)
        self._stub = general_python_service_pb2_grpc.GeneralPythonServiceStub(
            self._channel)

    def _pack_data_for_infer(self, feed_data):
        req = general_python_service_pb2.Request()
        for name, data in feed_data.items():
            if isinstance(data, list):
                data = np.array(data)
            elif not isinstance(data, np.ndarray):
                raise TypeError("only list and numpy array type is supported.")
            req.feed_var_names.append(name)
            req.feed_insts.append(data.tobytes())
            req.shape.append(np.array(data.shape, dtype="int32").tobytes())
            req.type.append(str(data.dtype))
        return req

    def predict(self, feed, fetch):
        if not isinstance(feed, dict):
            raise TypeError(
                "feed must be dict type with format: {name: value}.")
        if not isinstance(fetch, list):
            raise TypeError(
                "fetch_with_type must be list type with format: [name].")
        req = self._pack_data_for_infer(feed)
        resp = self._stub.inference(req)
        if resp.ecode != 0:
            raise Exception(resp.error_info)
        fetch_map = {}
        for idx, name in enumerate(resp.fetch_var_names):
            if name not in fetch:
                continue
            fetch_map[name] = np.frombuffer(
                resp.fetch_insts[idx], dtype=resp.type[idx])
            fetch_map[name].shape = np.frombuffer(
                resp.shape[idx], dtype="int32")
        return fetch_map
