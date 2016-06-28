import unittest
import yaml
from skopt import objectives as oo
import numpy as np
from pprint import pprint, pformat


class ParseWeightsKeyValueTest(unittest.TestCase):
    """Check correct parsing of key-value type of weight spec.
    """
    filedata = {
            'mh_GX_0': -0.27600000000000002,
            'mh_GK_0': -0.57899999999999996,
            'mh_GL_0': -0.73799999999999999,
            'mh_GX_2': -0.20399999999999999,
            'mh_GK_2': -0.14699999999999999,
            'mh_GL_2': -0.13900000000000001,
            'mh_GX_4': -0.23400000000000001,
            'mh_GK_4': -0.23400000000000001,
            'mh_GL_4': -0.23400000000000001,
            'me_GX_0': 0.91600000000000004,}
    dtype = [('keys','|S15'), ('values','float')]
    data = np.array([(k,v) for k,v in filedata.items()], dtype=dtype)

    def test_parse_weights_keyval_array(self):
        """Check correct parsing of explicit array of weights as spec.
        """
        spec = [ 4.,  1.,  1.,  4.,  1.,  1.,  1.,  1.,  1.,  1.]
        expected = np.array(spec)
        ww = oo.parse_weights_keyval(spec, self.data)
        compare = np.all(ww == expected)
        self.assertTrue(compare) 
        
    def test_parse_weights_keyval_keys(self):
        """Check correct parsing of key:value spec and data.
        """
        spec = { 'dflt': 1.,
                'me_GX_0': 4,
                'mh_GX_0': 4, }
        expected = np.ones(len(self.data))*spec.get('dflt', 0)
        for k,v in spec.items():
            if k != 'dflt':
                expected[self.data['keys']==k.encode()]=v
        ww = oo.parse_weights_keyval(spec, self.data)
        compare = np.all(ww == expected)
        self.assertTrue(compare)


class ParseWeightsTest(unittest.TestCase):
    """Check  correct parsing of weights with yaml spec.
    """
    yamldata = """subweights:
            dflt: 0 # default value of subweights
            indexes: # specific indexes of 1d-array
                - [0, 1]
                - [4, 4]
                - [2, 2.]
            ranges: # specific range in 1d-array
                - [[1,3], 2]
                - [[3,4], 5]
            nb: # range of bands in bands
                - [[-3, 0], 1.0] # all valence bands
                - [[0, 1], 2.0]   # top VB and bottom CB with higher weight
                - [[-1, 2], 0.5]   # some VB and some CB with somewhat higher weight
            eV: # range of energies in bands
                - [[-0.1, 0.], 4.0]
                - [[0.2, 0.5], 6.0]
            Ek: # specific band, k-point in bands
                - [[3, 9], 2.5]
                - [[1, 4], 3.5]
        """
    wspec = yaml.load(yamldata)['subweights']

    def check(self, result, expected):
        """The actual check"""
        compare = np.all(result == expected)
        self.assertTrue(compare, 
                msg="\nresult:\n{}\nexpected:\n{}".format(result, expected))

    def test_parse_weights_indexes(self):
        """Can we specify weights by a list of (index, weight) tuples?
        """
        dflt = self.wspec.get('dflt', 1.)
        # test weights for a 1D-type of data
        nn=5
        expected = np.ones(nn)*dflt
        expected[0] = 1.
        expected[4] = 4.
        expected[2] = 2.
        ww = oo.parse_weights(self.wspec, nn=nn, ikeys=['indexes'])
        self.check(ww, expected)

        # test weights for a 2D-type of data
        shape = (8, 10)
        expected = np.ones(shape)*dflt
        expected[3, 9] = 2.5
        expected[1, 4] = 3.5
        ww = oo.parse_weights(self.wspec, shape=shape, ikeys=['Ek'])
        self.check(ww, expected)
        
    def test_parse_weights_range_of_indexes(self):
        """Can we specify weights by a list of (index_range, weight) tuples?
        """
        shape = (8, 10)
        # note that counting starts from 0
        i0 = 3
        dflt = self.wspec.get('dflt', 1.)
        expected = np.ones(shape)*dflt
        # note that the spec range is interpreted as **inclusive** 
        # and has a non-zero reference index (i0)
        expected[0:4] = 1.
        expected[3:5] = 2.
        # note here that the lower value is ignored for bands assigned with
        # a higher weight already
        expected[5:6] = 0.5
        ww = oo.parse_weights(self.wspec, shape=shape, i0=i0, rikeys=['nb'])
        self.check(ww, expected)
        # alternative key for range specification
        expected = np.ones(shape)*dflt
        expected[1:4] = 2
        expected[3:5] = 5
        ww = oo.parse_weights(self.wspec, shape=shape, rikeys=['ranges'])
        self.check(ww, expected)

    def test_parse_weights_range_of_values(self):
        """Check we can specify weights via range of data values.
        """
        shape = (5, 5)
        data = np.array(
                [[ 0.42797684,  0.05719739, -0.06808132, -0.22651268, -0.03900927],
                [-0.18729846, -0.22162966, -0.09027381,  0.05959901, -0.46305776],
                [ 0.31494925,  0.23866489,  0.15701333,  0.11416699,  0.06721533],
                [ 0.45913109,  0.49479448,  0.29115756,  0.46113443, -0.05136717],
                [-0.28060449, -0.09965275, -0.28691529, -0.10078479,  0.40829291]])
        expected = np.array(
                [[ 6.,  0., 4., 0., 4.],
                [ 0., 0., 4., 0., 0.],
                [ 6., 6., 0., 0., 0.],
                [ 6., 6., 6., 6., 4.],
                [ 0., 4., 0., 0., 6.]])
        ww = oo.parse_weights(self.wspec, refdata=data, rfkeys=['eV'])
        self.check(ww, expected)
        
    def test_parse_weights_list_of_weights(self):
        altdata = """subweights: [1., 1., 2., 3., 5., 3., 2., 1., 1.]
            """
        wspec = yaml.load(altdata)['subweights']
        expected = yaml.load(altdata)['subweights']
        ww = oo.parse_weights(wspec, nn=len(wspec))
        self.check(ww, expected)

class GetModelsTest(unittest.TestCase):
    """Check if model names and weights are parsed correctly.
    """
    def test_get_models_str(self):
        """Can we get model name and weight of 1. from single string?
        """
        mm = 'Si/bs'
        expected = ('Si/bs', 1.0)
        models = oo.get_models(mm)
        self.assertSequenceEqual(models, expected)

    def test_get_models_list_of_str(self):
        """Can we get model names and weights of 1. from a list of string?
        """
        mm = ['Si/scc-3', 'Si/scc-2', 'Si/scc-1', 'Si', 'Si/scc+1', 'Si/scc+2', 'Si/scc+3']
        mm_names = mm
        mm_weights = [1.]*len(mm)
        expected = (mm_names, mm_weights)
        models = oo.get_models(mm)
        self.assertSequenceEqual(models, expected)

    def test_get_models_list_of_mw_tupples(self):
        """Can we get model names and weights from a list of (model_name,weight) tuples?
        """
        mm = [['SiO2-quartz/scc', 1.0], ['Si/scc', -0.5], ['O2/scc', -1]]
        mm_names = [m[0] for m in mm]
        mm_weights = [m[1] for m in mm]
        expected = (mm_names, mm_weights)
        models = oo.get_models(mm)
        self.assertSequenceEqual(models, expected)


class QueryTest(unittest.TestCase):
    """Test Query class and methods"""

    db1 = {}
    db2 = {}

    def check(self, result, expected):
        """The actual check"""
        compare = np.all(result == expected)
        self.assertTrue(compare, 
                msg="\nresult:\n{}\nexpected:\n{}".format(result, expected))

    def test_query_add_modeldb(self):
        """Can we add empty dictionaries to model data-base?
        """
        oo.Query.add_modeldb('d1', self.db1)
        oo.Query.add_modeldb('d2', self.db2)

        self.assertTrue(len(oo.Query.modeldb['d1'].items()) == 0)
        self.assertTrue(len(oo.Query.modeldb['d2'].items()) == 0)

    def test_query_update_modeldb(self):
        """Can we update model data-base and see update through instances?
        """
        oo.Query.modeldb['d1'] = {'a':1, 'b':2}
        oo.Query.modeldb['d2'] = {'a':3, 'b':4, 'c':7}
        q1 = oo.Query('d1', 'a')
        q2 = oo.Query(['d1', 'd2'], 'b')
        self.assertEqual(q1.modeldb['d1'], {'a':1, 'b':2}) 
        self.assertEqual(q2.modeldb['d2'], {'a':3, 'b':4, 'c':7})

    def test_query_single_model(self):
        """Can we get data from the query of single models?
        """
        oo.Query.modeldb['d1'] = {'a':1, 'b':2}
        q1 = oo.Query('d1', 'a')
        self.assertEqual(q1(), 1)

    def test_query_multiple_models(self):
        """Can we get data from the query of multiple models?
        """
        oo.Query.modeldb['d1'] = {'a':1, 'b':2}
        oo.Query.modeldb['d2'] = {'a':3, 'b':4, 'c':7}
        q2 = oo.Query(['d1', 'd2'], 'b')
        self.check(q2(), [2,4])


class ObjectiveRefDataTest(unittest.TestCase):
    """Check we can handle the 'ref:' item in the objectives input"""

    def check(self, result, expected):
        """The actual check"""
        compare = np.all(result == expected)
        self.assertTrue(compare, 
                msg="\nresult:\n{}\nexpected:\n{}".format(result, expected))

    def test_value(self):
        """Can we handle a single value and return an array?"""
        ref_input = 42
        expected = np.array(ref_input)
        result = oo.get_refdata(ref_input)
        self.check(result, expected)

    def test_array(self):
        """Can we handle an array or list and return an array?"""
        # try list
        ref_input = [1, 11, 42, 54]
        expected = np.array(ref_input)
        result = oo.get_refdata(ref_input)
        self.check(result, expected)
        # try 1D array
        ref_input = np.array([1, 11, 42, 54])
        expected = np.array(ref_input)
        result = oo.get_refdata(ref_input)
        self.check(result, expected)
        # try 2D array
        ref_input = np.array([1, 11, 42, 54, 3, 33]).reshape((2,3))
        expected = ref_input
        result = oo.get_refdata(ref_input)
        self.check(result, expected)

    def test_keyvalue_pairs(self):
        """Can we handle a dictionary with key-value pairs of data and return structured array?"""
        ref_input = { 'ab': 7, 'cd': 8 }
        expected = np.array
        dtype = [('keys','|S15'), ('values','float')]
        exp = np.array([(k,v) for k,v in ref_input.items()], dtype=dtype)
        res = oo.get_refdata(ref_input)
        self.check(res, exp)

    def test_file(self):
        """Can we handle dictionary spec with 'file:' item and read from file?"""
        ref_input = {'file': 'refdata_example.dat',
                'loader_args': {'unpack':False} }
        shape = (7,10)
        exp = np.array(list(range(shape[1]))*shape[0]).reshape(*shape)
        res = oo.get_refdata(ref_input)
        self.assertTrue(np.all(res==exp))
        # check default unpack works
        exp = np.transpose(exp)
        ref_input = {'file': 'refdata_example.dat',}
        res = oo.get_refdata(ref_input)
        self.assertTrue(np.all(res==exp), 
                msg='\nexp: {}\nres:{}'.format(exp, res))
        
    def test_process(self):
        """Can we handle file data and post-process it?"""
        ref_input = {'file': 'refdata_example.dat',
                     'loader_args': {'unpack':False} ,
                     'process': {'scale': 2.,
                                 'rm_columns': [1, [2, 4],],
                                 'rm_rows': [1, 3, [5,7]]}}
        shape = (7,10)
        exp = np.array(list(range(shape[1]))*shape[0]).reshape(*shape)
        exp = np.delete(exp, obj=[0, 2, 4, 5, 6], axis=0)
        exp = np.delete(exp, obj=[0, 1, 2, 3], axis=1)
        exp = exp * 2.
        res = oo.get_refdata(ref_input)
        self.check(res, exp)
        

class GetRangesTest(unittest.TestCase):
    """Test we interpret range specifications correctly"""

    def test_f2prange_single(self):
        """Check fortran to python range conversion for 1-wide range"""
        rng = (2,2)
        expected = (1,2)
        result = oo.f2prange(rng)
        self.assertEqual(result, expected)

    def test_f2prange_wide(self):
        """Check fortran to python range conversion for wide range"""
        rng = (2,20)
        expected = (1,20)
        result = oo.f2prange(rng)
        self.assertEqual(result, expected)

    def test_getranges_singleindex(self):
        """Can we translate single index to python range spec?"""
        data = 42
        exp = [(41,42)]
        res = oo.getranges(data)
        self.assertEqual(res, exp, msg="r:{}, e:{}".format(res, exp))

    def test_getranges_listofindexes(self):
        """Can we translate list of indexes to python range spec?"""
        data = [42, 33, 1, 50]
        exp = [(41,42), (32,33), (0,1), (49,50)]
        res = oo.getranges(data)
        self.assertEqual(res, exp, msg="r:{}, e:{}".format(res, exp))

    def test_getranges_listofranges(self):
        """Can we translate list of ranges to python range spec?"""
        data = [[3, 33], [1, 50]]
        exp = [(2,33), (0,50)]
        res = oo.getranges(data)
        self.assertEqual(res, exp, msg="r:{}, e:{}".format(res, exp))

    def test_getranges_mix_indexesandranges(self):
        """Can we translate list of ranges to python range spec?"""
        data = [7, 42, [3, 33], [1, 50], 5]
        exp = [(6, 7), (41,42), (2,33), (0,50), (4,5)]
        res = oo.getranges(data)
        self.assertEqual(res, exp, msg="r:{}, e:{}".format(res, exp))


class ObjectiveTypesTest(unittest.TestCase):
    """Can we create objectives of different types?"""
    
    def check(self, result, expected):
        """The actual check"""
        compare = np.all(result == expected)
        self.assertTrue(compare, 
                msg="\nresult:\n{}\nexpected:\n{}".format(result, expected))

    def test_objtype_values_single_model(self):
        """Can we create value-type objective for a single model"""
        yamldata = """objectives:
            - band_gap:
                models: Si/bs
                ref: 1.12
                weight: 3.0
        """
        dat = 1.2
        ow  = 1.
        spec = yaml.load(yamldata)['objectives']
        ref = spec[0]['band_gap']['ref']
        www = spec[0]['band_gap']['weight']
        mnm = spec[0]['band_gap']['models']
        # set data base
        db = {}
        oo.Query.add_modeldb('Si/bs', db)
        # check declaration
        objv = oo.set_objectives(spec)[0]
        self.assertEqual(objv.model_names, mnm)
        self.assertEqual(objv.model_weights, ow)
        self.assertEqual(objv.weight, www)
        self.assertEqual(objv.ref_data, ref)
        self.assertEqual(objv.subweights, ow)
        self.assertEqual(objv.query_key, 'band_gap')
        # check __call__()
        db['band_gap'] = dat
        mdat, rdat, weights = objv()
        self.assertEqual(mdat, dat)
        self.assertEqual(rdat, ref)
        self.assertEqual(weights, ow)
        

    def test_objtype_values_multiple_models(self):
        """Can we create a value-type objective from several models"""
        yamldata = """objectives:
            - Etot:
                models: [Si/scc-1, Si/scc, Si/scc+1,]
                ref: [23., 10, 15.]
                options:
                        subweights: [1., 3., 1.,]
        """
        spec = yaml.load(yamldata)['objectives']
        ref = spec[0]['Etot']['ref']
        mnm = spec[0]['Etot']['models']
        subw = [1., 3., 1.]
        # check declaration
        objv = oo.set_objectives(spec)[0]
        self.assertEqual(objv.model_names, mnm)
        self.assertEqual(objv.weight, 1)
        self.check(objv.model_weights, [1]*3)
        self.check(objv.ref_data, ref)
        self.check(objv.subweights, subw)
        self.assertEqual(objv.query_key, 'Etot')
        # set data base: 
        # could be done either before or after declaration
        db1, db2, db3 = {}, {}, {}
        oo.Query.add_modeldb('Si/scc-1', db1)
        oo.Query.add_modeldb('Si/scc', db2)
        oo.Query.add_modeldb('Si/scc+1', db3)
        dat = [20, 12, 16]
        db1['Etot'] = dat[0]
        db2['Etot'] = dat[1]
        db3['Etot'] = dat[2]
        # check __call__()
        mdat, rdat, weights = objv()
        self.check(mdat, dat)
        self.check(rdat, ref)
        self.check(weights, subw)
        

    def test_objtype_keyvaluepairs(self):
        """Can we create objective from given key-value pairs"""

    def test_objtype_weightedsum(self):
        """Can we create objective from pairs of value-weight"""
        yamldata = """objectives:
            - weighted_sum:
                doc: "heat of formation, SiO2"
                models: 
                    - [SiO2-quartz/scc, 1.]
                    - [Si/scc, -0.5] 
                    - [O2/scc, -1]
                query: Etot 
                ref: 1.8 
                weight: 1.2
        """
        spec = yaml.load(yamldata)['objectives']
        ref = spec[0]['weighted_sum']['ref']
        doc = spec[0]['weighted_sum']['doc']
        oww = spec[0]['weighted_sum']['weight']
        mnm = [m[0] for m in spec[0]['weighted_sum']['models']]
        mww = np.array([m[1] for m in spec[0]['weighted_sum']['models']])
        subw = 1.
        print (doc, ref, oww, mnm, mww)
        # check declaration
        objv = oo.set_objectives(spec)[0]
#        self.assertEqual(objv.doc, doc)
        self.assertEqual(objv.weight, oww)
        self.assertEqual(objv.model_names, mnm)
        self.check(objv.model_weights, mww)
        self.assertEqual(objv.ref_data, ref)
        self.assertEqual(objv.subweights, subw)
        self.assertEqual(objv.query_key, 'Etot')
        # set data base: 
        # could be done either before or after declaration
        db1, db2, db3 = {}, {}, {}
        oo.Query.add_modeldb('SiO2-quartz/scc', db1)
        oo.Query.add_modeldb('Si/scc', db2)
        oo.Query.add_modeldb('O2/scc', db3)
        dat = [20, 12, 16]
        db1['Etot'] = dat[0]
        db2['Etot'] = dat[1]
        db3['Etot'] = dat[2]
        # check __call__()
        mdat, rdat, weights = objv()
        self.check(mdat, np.dot(np.asarray(dat), np.asarray(mww)))
        self.check(rdat, ref)
        self.check(weights, subw)

    def test_objtype_bands(self):
        """Can we create objective from spec for bands"""
        pass

#class SetObjectivesTest(unittest.TestCase):
#    """Check if we can create objectives from yaml definition"""


if __name__ == '__main__':
    unittest.main()

