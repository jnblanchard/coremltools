import unittest
import numpy as np
import coremltools
from coremltools.models import MLModel
from coremltools._deps import HAS_KERAS_TF


if HAS_KERAS_TF:
    from keras.models import Sequential
    from keras.layers import Dense, LSTM
    from coremltools.converters import keras as keras_converter


@unittest.skipIf(not HAS_KERAS_TF, 'Missing keras. Skipping tests.')
class BasicNumericCorrectnessTest(unittest.TestCase):
    
    def test_classifier(self):
        np.random.seed(1988)
        
        print('running test classifier')
        
        input_dim = 5
        num_hidden = 12
        num_classes = 6
        input_length = 3
        
        model = Sequential()
        model.add(LSTM(num_hidden, input_dim=input_dim, input_length=input_length, return_sequences=False))
        model.add(Dense(num_classes, activation='softmax'))
        
        model.set_weights([np.random.rand(*w.shape) for w in model.get_weights()])
        
        input_names = ['input']
        output_names = ['zzzz']
        class_labels = ['a', 'b', 'c', 'd', 'e', 'f']
        predicted_feature_name = 'pf'
        coremlmodel = keras_converter.convert(model, input_names, output_names, class_labels=class_labels, predicted_feature_name=predicted_feature_name, predicted_probabilities_output=output_names[0])
    
        inputs = np.random.rand(input_dim)
        outputs = coremlmodel.predict({'input': inputs})
        # this checks that the dictionary got the right name and type
        self.assertEquals(type(outputs[output_names[0]]), type({'a': 0.5}))
    
    def test_classifier_no_name(self):
        np.random.seed(1988)
        
        input_dim = 5
        num_hidden = 12
        num_classes = 6
        input_length = 3
        
        model = Sequential()
        model.add(LSTM(num_hidden, input_dim=input_dim, input_length=input_length, return_sequences=False))
        model.add(Dense(num_classes, activation='softmax'))
        
        model.set_weights([np.random.rand(*w.shape) for w in model.get_weights()])
        
        input_names = ['input']
        output_names = ['zzzz']
        class_labels = ['a', 'b', 'c', 'd', 'e', 'f']
        predicted_feature_name = 'pf'
        coremlmodel = keras_converter.convert(model, input_names, output_names, class_labels=class_labels, predicted_feature_name=predicted_feature_name)
        
        inputs = np.random.rand(input_dim)
        outputs = coremlmodel.predict({'input': inputs})
        # this checks that the dictionary got the right name and type
        self.assertEquals(type(outputs[output_names[0]]), type({'a': 0.5}))
    
    def test_internal_layer(self):
        
        np.random.seed(1988)
        
        input_dim = 5
        num_channels1 = 10
        num_channels2 = 7
        num_channels3 = 5
        
        w1 = (np.random.rand(input_dim, num_channels1)-0.5)/5.0;
        w2 = (np.random.rand(num_channels1, num_channels2)-0.5)/5.0;
        w3 = (np.random.rand(num_channels2, num_channels3)-0.5)/5.0;
        
        b1 = (np.random.rand(num_channels1,)-0.5)/5.0;
        b2 = (np.random.rand(num_channels2,)-0.5)/5.0;
        b3 = (np.random.rand(num_channels3,)-0.5)/5.0;
        
        model = Sequential()
        model.add(Dense(num_channels1, input_dim = input_dim))
        model.add(Dense(num_channels2, name='middle_layer'))
        model.add(Dense(num_channels3))
        
        model.set_weights([w1, b1, w2, b2, w3, b3])
        
        input_names = ['input']
        output_names = ['output']
        coreml1 = keras_converter.convert(model, input_names, output_names)
        
        # adjust the output parameters of coreml1 to include the intermediate layer
        spec = coreml1.get_spec()
        coremlNewOutputs = spec.description.output.add()
        coremlNewOutputs.name = 'middle_layer_output'
        coremlNewParams = coremlNewOutputs.type.multiArrayType
        coremlNewParams.dataType = coremltools.proto.FeatureTypes_pb2.ArrayFeatureType.ArrayDataType.Value('DOUBLE')
        coremlNewParams.shape.extend([num_channels2])
        
        coremlfinal = coremltools.models.MLModel(spec)
        
        # generate a second model which
        model2 = Sequential()
        model2.add(Dense(num_channels1, input_dim = input_dim))
        model2.add(Dense(num_channels2))
        model2.set_weights([w1, b1, w2, b2])
        
        coreml2 = keras_converter.convert(model2, input_names, ['output2'])
        
        # generate input data
        inputs = np.random.rand(input_dim)

        fullOutputs = coremlfinal.predict({'input': inputs})
        
        partialOutput = coreml2.predict({'input': inputs})
        
        for i in range(0, num_channels2):
            self.assertAlmostEquals(fullOutputs['middle_layer_output'][i], partialOutput['output2'][i], 2)
            

