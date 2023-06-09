"""
 Copyright (c) 2019 Intel Corporation

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""

from openvino.inference_engine import  IECore  # pylint: disable=no-name-in-module
def load_ie_core(device, cpu_extension=None):
    """Loads IE Core"""

    ie = IECore()
    if device == "CPU" and cpu_extension:
        ie.add_extension(cpu_extension, "CPU")

    return ie


class IEModel:  # pylint: disable=too-few-public-methods
    """ Class that allows worknig with Inference Engine model. """

    def __init__(self, model_path, device, ie_core, num_requests):
        """Constructor"""
        if model_path.endswith((".xml", ".bin")):
            model_path = model_path[:-4]
        model_xml = model_path + ".xml"
        model_bin = model_path + ".bin"
        self.net = ie_core.read_network(model=model_xml, weights=model_bin)
        #assert len(self.net.inputs.keys()) == 1, "One input is expected"

        supported_layers = ie_core.query_network(self.net, device)
        not_supported_layers = [l for l in self.net.layers.keys() if l not in supported_layers]
        if len(not_supported_layers) > 0:
            raise RuntimeError("Following layers are not supported by the {} plugin:\n {}"
                               .format(device, ', '.join(not_supported_layers)))

        self.exec_net = ie_core.load_network(network=self.net,
                                             device_name=device,
                                             num_requests=num_requests)
        input_info = self.net.input_info
        self.input_name = next(iter(input_info))
        #self.input_name = next(iter(self.net.input_data))
        
        if len(self.net.outputs) > 1:
            
            candidates = []
            for candidate_name in self.net.outputs:
                candidates.append(candidate_name)
            self.output_name = candidates
           
        else:
            self.output_name = next(iter(self.net.outputs))

        #self.input_size = self.net.inputs[self.input_name].shape
        #self.output_size = self.exec_net.requests[0].outputs[self.output_name].shape
        self.input_size = self.net.input_info[self.input_name].input_data.shape
        
        self.num_requests = num_requests

    def infer(self, data):
        """Runs model on the specified input"""

        input_data = {self.input_name: data}
        infer_result = self.exec_net.infer(input_data)
       
        if type(self.output_name).__name__ == 'list':
            results = []
            for output_item in self.output_name:
                results.append(infer_result[output_item])
            return results
        else:
            return infer_result[self.output_name]

    def async_infer(self, data, req_id):
        """Requests model inference for the specified input"""

        input_data = {self.input_name: data}
        self.exec_net.start_async(request_id=req_id, inputs=input_data)

    def wait_request(self, req_id):
        """Waits for the model output by the specified request ID"""

        if self.exec_net.requests[req_id].wait(-1) == 0:
            return self.exec_net.requests[req_id].outputs[self.output_name]
        else:
            return None
