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


import cv2
import numpy as np

from tools.common import IEModel
import os

char_num = 13
class Model(IEModel):
    """ Class that allows worknig with person detectpr models. """

    def __init__(self, model_path, device, ie_core, num_requests = 1):
        """Constructor"""

        super().__init__(model_path, device, ie_core, num_requests)
        _, _, h, w = self.input_size
        self.input_height = h
        self.input_width = w
        
        keys_path = os.path.join(os.path.dirname(model_path),'keys.txt')
        keys_file = open(keys_path, 'r', encoding ='utf-8')
        self.alphabet  = keys_file.readline().rstrip()


    def _prepare_frame(self, img):
        """Converts input image according model requirements"""
        img=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        img = cv2.resize(img,(self.input_width,self.input_height))  
        img = img.reshape([1, 1,self.input_height, self.input_width])
        return img
        

    def _process_output(self,pred):
        """Converts network output to text"""
        seq_len = int(120/4)
        pred = pred.transpose((1,0,2)).reshape((1,seq_len,char_num))
        pred = pred[0,:,:]
        
        
        characters = self.alphabet[:]
        characters = characters[:] + u'卍'
        nclass = len(characters)
      
        res = ""
        prev_pad = False
        pred = np.expand_dims(pred, axis=0)
        pred_idx = pred.argmax(axis=2)[0]
        
        for idx in pred_idx:
            pred_text = characters[idx]
            if pred_text != u'卍':
                if(len(res) == 0 or prev_pad or (len(res)!= 0 and pred_text!= res[-1])):
                    prev_pad = False
                    res = res + pred_text
            else:
                prev_pad = True
        return res
    
    def __call__(self, frame):
        """Runs model on the specified input"""
        outs = []
        in_frame = self._prepare_frame(frame)
        result = self.infer(in_frame)
        out = self._process_output(result)
        return out
