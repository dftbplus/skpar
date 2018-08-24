import unittest
import logging
import numpy as np
import numpy.testing as nptest
import yaml
from skpar.core import objectives as oo
from skpar.core.database import Database, Query
from skpar.core.evaluate import relerr
np.set_printoptions(precision=3, formatter={'float_kind':lambda x: "%.2f" % x})

logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(format='%(message)s')
logger = logging.getLogger(__name__)


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
    dtype = [('keys','S15'), ('values','float')]
    data = np.array([(k,v) for k,v in filedata.items()], dtype=dtype)

    def test_parse_weights_keyval_array(self):
        """Check correct parsing of explicit array of weights as spec.
        """
        spec = [ 4.,  1.,  1.,  4.,  1.,  1.,  1.,  1.,  1.,  1.]
        expected = np.array(spec)
        ww = oo.parse_weights_keyval(spec, self.data, normalised=False)
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
        ww = oo.parse_weights_keyval(spec, self.data, normalised=False)
        compare = np.all(ww == expected)
        self.assertTrue(compare)


class ParseWeightsTest(unittest.TestCase):
    """Check  correct parsing of weights with yaml spec.
    """
    yamldata = """subweights:
            # indexes and ranges are specified in FORTRAN style
            dflt: 0 # default value of subweights
            indexes: # specific indexes of 1d-array
                - [1, 2]
                - [4, 4]
                - [2, 2]
            ranges: # specific range in 1d-array
                - [[1,3], 2]
                - [[3,4], 5]
            nb: # range of bands in bands
                - [[1, 4], 1.0]   # e.g. all valence bands in sp-basis
                - [[3, 4], 2.0]   # top VB and bottom CB with higher weight
                - [[4, 5], 3.5]   # some VB and some CB with somewhat higher weight
            eV: # range of energies in bands
                - [[-0.1, 0.], 4.0]
                - [[0.2, 0.5], 6.0]
            Ek: # specific band, k-point in bands
                - [[4, 10], 2.5]
                - [[2, 5], 3.5]
        """
    wspec = yaml.load(yamldata)['subweights']

    def test_parse_weights_indexes(self):
        """Can we specify weights by a list of (index, weight) tuples?
        """
        dflt = self.wspec.get('dflt', 1.)
        # test weights for a 1D-type of data
        nn=5
        expected = np.ones(nn)*dflt
        expected[0] = 2.
        expected[3] = 4.
        expected[1] = 2.
        ww = oo.parse_weights(self.wspec, nn=nn, ikeys=['indexes'], normalised=False)
        nptest.assert_array_equal(ww, expected, verbose=True)

        # test weights for a 2D-type of data
        shape = (8, 10)
        expected = np.ones(shape)*dflt
        expected[3, 9] = 2.5
        expected[1, 4] = 3.5
        ww = oo.parse_weights(self.wspec, shape=shape, ikeys=['Ek'], normalised=False)
        nptest.assert_array_equal(ww, expected, verbose=True)
        
    def test_parse_weights_range_of_indexes(self):
        """Can we specify weights by a list of (index_range, weight) tuples?
        """
        shape = (8, 10)
        # note that counting starts from 0
        i0 = 0
        dflt = self.wspec.get('dflt', 1.)
        expected = np.ones(shape)*dflt
        # note that the spec range is interpreted as **inclusive** 
        # and has a non-zero reference index (i0)
        expected[0:4] = 1.
        expected[2:4] = 2.
        # note here that the lower value is ignored for bands assigned with
        # a higher weight already
        expected[3:5] = 3.5
        ww = oo.parse_weights(self.wspec, shape=shape, i0=i0, rikeys=['nb'], 
                                normalised=False)
        nptest.assert_array_equal(ww, expected, verbose=True)
        # alternative key for range specification
        expected = np.ones(shape)*dflt
        expected[0:3] = 2
        expected[2:4] = 5
        ww = oo.parse_weights(self.wspec, shape=shape, rikeys=['ranges'],
                                normalised=False)
        nptest.assert_array_equal(ww, expected, verbose=True)

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
        ww = oo.parse_weights(self.wspec, refdata=data, rfkeys=['eV'],
                                normalised=False)
        nptest.assert_array_equal(ww, expected, verbose=True)
        
    def test_parse_weights_list_of_weights(self):
        altdata = """subweights: [1., 1., 2., 3., 5., 3., 2., 1., 1.]
            """
        wspec = yaml.load(altdata)['subweights']
        expected = yaml.load(altdata)['subweights']
        ww = oo.parse_weights(wspec, nn=len(wspec), normalised=False)
        nptest.assert_array_equal(ww, expected, verbose=True)


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


class ObjectiveRefDataTest(unittest.TestCase):
    """Check we can handle the 'ref:' item in the objectives input"""

    def test_value(self):
        """Can we handle a single value and return an array with (1,) shape?"""
        ref_input = 42
        expected = np.array([ref_input,])
        result = oo.get_refdata(ref_input)
        self.assertEqual(result.shape, (1,))
        nptest.assert_array_equal(result, expected, verbose=True)

    def test_array(self):
        """Can we handle an array or list and return an array?"""
        # try list
        ref_input = [1, 11, 42, 54]
        expected = np.array(ref_input)
        result = oo.get_refdata(ref_input)
        nptest.assert_array_equal(result, expected, verbose=True)
        # try 1D array
        ref_input = np.array([1, 11, 42, 54])
        expected = np.array(ref_input)
        result = oo.get_refdata(ref_input)
        nptest.assert_array_equal(result, expected, verbose=True)
        # try 2D array
        ref_input = np.array([1, 11, 42, 54, 3, 33]).reshape((2,3))
        expected = ref_input
        result = oo.get_refdata(ref_input)
        nptest.assert_array_equal(result, expected, verbose=True)

    def test_keyvalue_pairs(self):
        """Can we handle a dictionary with key-value pairs of data and return structured array?"""
        ref_input = { 'ab': 7, 'cd': 8 }
        expected = np.array
        dtype = [('keys','S15'), ('values','float')]
        exp = np.array([(k,v) for k,v in ref_input.items()], dtype=dtype)
        res = oo.get_refdata(ref_input)
        nptest.assert_array_equal(res, exp, verbose=True)

    def test_file(self):
        """Can we handle dictionary spec with 'file:' item and read from file?"""
        ref_input = {'file': './reference_data/refdata_example.dat',
                'loader_args': {'unpack':False} }
        shape = (7, 10) # expect 7-row, 10-col data
        exp = np.array(list(range(shape[1]))*shape[0]).reshape(*shape)
        res = oo.get_refdata(ref_input)
        nptest.assert_array_equal(res, exp, verbose=True)
        # check default unpack works
        exp = np.transpose(exp)
        ref_input = {'file': './reference_data/refdata_example.dat',
                'loader_args': {'unpack':True} }
        res = oo.get_refdata(ref_input)
        nptest.assert_array_equal(res, exp, verbose=True)
        
    def test_process(self):
        """Can we handle file data and post-process it?"""
        ref_input = {'file': './reference_data/refdata_example.dat',
                     'loader_args': {'unpack':False} ,
                     'process': {'scale': 2.,
                                 'rm_columns': [1, [2, 4],],
                                 'rm_rows': [1, 3, [5,7]]}}
        shape = (7, 10) # expect 7-row, 10-col data
        exp = np.array(list(range(shape[1]))*shape[0]).reshape(*shape)
        exp = np.delete(exp, obj=[0, 2, 4, 5, 6], axis=0)
        exp = np.delete(exp, obj=[0, 1, 2, 3], axis=1)
        exp = exp * 2.
        res = oo.get_refdata(ref_input)
        nptest.assert_array_equal(res, exp, verbose=True)


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
        res = oo.get_ranges(data)
        self.assertEqual(res, exp, msg="r:{}, e:{}".format(res, exp))

    def test_getranges_listofindexes(self):
        """Can we translate list of indexes to python range spec?"""
        data = [42, 33, 1, 50]
        exp = [(41,42), (32,33), (0,1), (49,50)]
        res = oo.get_ranges(data)
        self.assertEqual(res, exp, msg="r:{}, e:{}".format(res, exp))

    def test_getranges_listofranges(self):
        """Can we translate list of ranges to python range spec?"""
        data = [[3, 33], [1, 50]]
        exp = [(2,33), (0,50)]
        res = oo.get_ranges(data)
        self.assertEqual(res, exp, msg="r:{}, e:{}".format(res, exp))

    def test_get_ranges_mix_indexesandranges(self):
        """Can we translate list of ranges to python range spec?"""
        data = [7, 42, [3, 33], [1, 50], 5]
        exp = [(6, 7), (41,42), (2,33), (0,50), (4,5)]
        res = oo.get_ranges(data)
        self.assertEqual(res, exp, msg="r:{}, e:{}".format(res, exp))


class GetSubsetIndTest(unittest.TestCase):
    """Can we obtain an index array from a specification of a given set of ranges"""

    def test_singlerange(self):
        """Check we get an index array from multiple ranges"""
        rangespec = yaml.load("""range: [ 1, 3, [4, 6], 8]""")['range']
        expected = np.array([0, 2, 3, 4, 5, 7])
        result = oo.get_subset_ind(rangespec)
        nptest.assert_array_equal(result, expected, verbose=True)


class GetObjTypeTest(unittest.TestCase):
    """Can we guess the type of objective from its spec?"""

    def test_getobjtype_default(self):
        """Can we try to guess, fail, and return default?"""
        nmod = 1
        ref = np.random.rand((1))
        objtype = oo.get_type(nmod, ref, dflt_type='unknown')
        self.assertEqual(objtype, 'unknown')
        nmod = 1
        ref = np.random.rand((1))
        objtype = oo.get_type(nmod, ref)
        self.assertEqual(objtype, 'values')
        nmod = 3
        ref = np.random.rand((3))
        objtype = oo.get_type(nmod, ref)
        self.assertEqual(objtype, 'values')

    def test_getobjtype_values(self):
        """Can we guess objective is of type 'values'?"""
        # one model, one value
        nmod = 1
        ref = np.random.rand(1)
        objtype = oo.get_type(nmod, ref)
        self.assertEqual(objtype, 'values')
        # many models, as many values
        nmod = 3
        ref = np.random.rand(3)
        objtype = oo.get_type(nmod, ref)
        self.assertEqual(objtype, 'values')

    def test_getobjtype_keyvaluepairs(self):
        """Can we guess objective is of type 'keyvalpairs'?"""
        nmod = 1
        filedata = {
            'mh_GX_0': -0.27600000000000002,
            'mh_GK_0': -0.57899999999999996,
            'mh_GL_0': -0.73799999999999999,
           'me_GX_0': 0.91600000000000004,}
        dtype = [('keys','S15'), ('values','float')]
        ref = np.array([(k,v) for k,v in filedata.items()], dtype=dtype)
        objtype = oo.get_type(nmod, ref)
        self.assertEqual(objtype, 'keyval_pairs')

    def test_getobjtype_weightedsum(self):
        """Can we guess objective is of type 'weighted_sum'?"""
        nmod = 5
        ref = np.random.rand(1)
        objtype = oo.get_type(nmod, ref)
        self.assertEqual(objtype, 'weighted_sum')

    def test_getobjtype_bands(self):
        """Can we guess objective is of type 'bands'?"""
        nmod = 1
        ref = np.random.rand(3, 9)
        objtype = oo.get_type(nmod, ref)
        self.assertEqual(objtype, 'bands')


class ObjectiveTypesTest(unittest.TestCase):
    """Can we create objectives of different types?"""

    def test_objtype_values_single_model_single_data(self):
        """Can we create value-type objective for a single model"""
        yamldata = """objectives:
            - band_gap:
                doc: Band gap, Si
                models: Si/bs
                ref: 1.12
                weight: 3.0
        """
        dat = 1.2
        ow  = 1.
        spec = yaml.load(yamldata)['objectives'][0]
        que = 'band_gap'
        ref = 1.12
        www = 3.0
        mnm = 'Si/bs'
        # set data base
        database = Database()
        database.update('Si/bs')
        modeldb = database.get('Si/bs')
        # check declaration
        objv = oo.get_objective(spec)
        self.assertEqual(objv.objtype, 'values')
        self.assertEqual(objv.model_names, mnm)
        self.assertEqual(objv.model_weights, ow)
        self.assertEqual(objv.weight, www)
        self.assertEqual(objv.ref_data, ref)
        self.assertEqual(objv.subweights, ow)
        self.assertEqual(objv.query_key, que)
        # check __call__()
        modeldb['band_gap'] = dat
        mdat, rdat, weights = objv.get(database)
        self.assertEqual(mdat, dat)
        self.assertEqual(rdat, ref)
        self.assertEqual(weights, ow)

    def test_objtype_values_single_model_array_data(self):
        """Can we create 1d-array-values-type objective for a single model"""
        yamldata = """objectives:
            - Etot(Vol):
                doc: 'Energy-Volume dependnce of Wurtziteac structure'
                models: GaN-W-ac 
                ref: [-20.236, -21.099, -21.829, -22.45, -22.967,
                    -23.387, -23.719, -23.974, 
                    -24.158, -24.278, -24.304, -24.348, -24.309,
                    -24.228, -24.11 , -23.952, 
                    -23.769, -23.559, -23.328, -23.076, -22.809]
                options:
                    subweights: [1,1,1,1,1, 2,2,2, 3,3,3,3,3, 2,2,2, 1,1,1,1,1]
        """
        data = [-20.24,-21.1,-21.83,-22.45,-22.97,
            -23.4,-23.72,-23.97,
            -24.2,-24.3,-24.3,-24.35,-24.31, 
            -24.23,-24.11,-23.9,
            -23.77,-23.56,-23.3,-23.1,-22.8]
        logger.info(data)
        que = 'Etot(Vol)'
        ref = [-20.236, -21.099, -21.829, -22.45,-22.967,
                    -23.387, -23.719, -23.974,
                    -24.158, -24.278, -24.304,  -24.348, -24.309, 
                    -24.228, -24.11,  -23.952,
                    -23.769, -23.559, -23.328,  -23.076, -22.809]
        sbw = [1,1,1,1,1, 2,2,2, 3,3,3,3,3, 2,2,2, 1,1,1,1,1]
        sbw = np.asarray(sbw)/np.sum(sbw) # normalise
        model = 'GaN-W-ac'
        # set data base
        database = Database()
        database.update(model)
        modeldb = database.get(model)
        # check declaration
        spec = yaml.load(yamldata)['objectives'][0]
        logger.info(spec)
        objv = oo.get_objective(spec)
        self.assertEqual(objv.model_names, model)
        self.assertEqual(objv.model_weights, 1.)
        self.assertEqual(objv.weight, 1)
        nptest.assert_array_equal(objv.ref_data, ref, verbose=True)
        nptest.assert_array_equal(objv.subweights, sbw, verbose=True)
        self.assertEqual(objv.query_key, que)
        self.assertEqual(objv.objtype, 'values')
        # check __call__()
        modeldb[que] = data
        mdata, rdata, weights = objv.get(database)
        nptest.assert_array_equal(mdata, data, verbose=True)
        nptest.assert_array_equal(rdata, ref, verbose=True)
        nptest.assert_array_equal(weights, sbw, verbose=True)

    def test_objtype_values_multiple_models(self):
        """Can we create a value-type objective from several models"""
        yamldata = """objectives:
            - Etot:
                doc: Energy vs volume, Si
                models: [Si/scc-1, Si/scc, Si/scc+1,]
                ref: [23., 10, 15.]
                options:
                    normalise: false
                    subweights: [1., 3., 1.,]
        """
        spec = yaml.load(yamldata)['objectives'][0]
        que = 'Etot'
        ref = [23., 10, 15.]
        mnm = ['Si/scc-1', 'Si/scc', 'Si/scc+1',]
        subw = [1., 3., 1.]
        # check declaration
        objv = oo.get_objective(spec)
        self.assertEqual(objv.model_names, mnm)
        self.assertEqual(objv.weight, 1)
        nptest.assert_array_equal(objv.model_weights, [1]*3, verbose=True)
        nptest.assert_array_equal(objv.ref_data, ref, verbose=True)
        nptest.assert_array_equal(objv.subweights, subw, verbose=True)
        self.assertEqual(objv.query_key, que)
        # set data base: 
        # could be done either before or after declaration
        database = Database()
        database.update('Si/scc-1')
        database.update('Si/scc')
        database.update('Si/scc+1')
        dat = [20, 12, 16]
        database.update('Si/scc-1', {'Etot': dat[0]})
        database.update('Si/scc', {'Etot': dat[1]})
        database.update('Si/scc+1', {'Etot': dat[2]})
        # check __call__()
        mdat, rdat, weights = objv.get(database)
        nptest.assert_array_equal(mdat, dat, verbose=True)
        nptest.assert_array_equal(rdat, ref, verbose=True)
        nptest.assert_array_equal(weights, subw, verbose=True)

    def test_objtype_keyvaluepairs(self):
        """Can we create objective from given key-value pairs"""
        yamldata = """objectives:
            - meff:
                doc: Effective masses, Si
                models: Si/bs
                ref: 
                    file: ./reference_data/meff-Si.dat
                    loader_args: 
                        dtype:
                        # NOTABENE: yaml cannot read in tuples, so we must
                        #           use the dictionary formulation of dtype
                            names: ['keys', 'values']
                            formats: ['S15', 'float']
                options:
                    normalise: false
                    subweights: 
                        # consider only a couple of entries from available data
                        dflt: 0.
                        me_GX_0: 2.
                        mh_GX_0: 1.
                weight: 1.5
        """
        spec = yaml.load(yamldata)['objectives'][0]
        que = 'meff'
        # NOTABENE: order here must coincide with order in ref:file
        ref = np.array([('me_GX_0', 0.916), ('mh_GX_0', -0.276)],
                       dtype=[('keys', 'S15'), ('values', 'float')])
        ref = ref['values']
        subw = np.array([2., 1.])
        doc = spec[que]['doc']
        oww = spec[que]['weight']
        mnm = spec[que]['models']
        # check declaration
        objv = oo.get_objective(spec)
        logger.debug(objv)
        self.assertEqual(objv.doc, doc)
        self.assertEqual(objv.weight, oww)
        self.assertEqual(objv.model_names, mnm)
        self.assertEqual(objv.model_weights, 1.)
        nptest.assert_array_equal(objv.ref_data, ref, verbose=True)
        nptest.assert_array_equal(objv.subweights, subw, verbose=True)
        self.assertEqual(objv.query_key, ['me_GX_0', 'mh_GX_0'])
        self.assertEqual(objv.objtype, 'keyval_pairs')
        # set data base: 
        # could be done either before or after declaration
        database = Database()
        dat = [0.9, -0.5, 1.2]
        database.update('Si/bs', {'me_GX_0': dat[0], 'mh_GX_0': dat[1],
                                     'me_GL_2':dat[2]})
        # check __call__()
        mdat, rdat, weights = objv.get(database)
        #logger.debug(mdat)
        #logger.debug(rdat)
        #logger.debug(weights)
        # NOTABENE: order depends on the order in the reference file!!!
        nptest.assert_array_equal(mdat, np.asarray(dat[0:2]), verbose=True)
        nptest.assert_array_equal(rdat, ref, verbose=True)
        nptest.assert_array_equal(weights, subw, verbose=True)

    def test_objtype_weightedsum(self):
        """Can we create objective from pairs of value-weight"""
        yamldata = """objectives:
            - Etot:
                doc: "heat of formation, SiO2"
                models: 
                    - [SiO2-quartz/scc, 1.]
                    - [Si/scc, -0.5] 
                    - [O2/scc, -1]
                ref: 1.8 
                weight: 1.2
        """
        spec = yaml.load(yamldata)['objectives'][0]
        que = 'Etot'
        ref = spec[que]['ref']
        doc = spec[que]['doc']
        oww = spec[que]['weight']
        mnm = [m[0] for m in spec[que]['models']]
        mww = np.asarray([m[1] for m in spec[que]['models']])
        subw = 1.
        # set data base: 
        # could be done either before or after declaration
        database = Database()
        # check declaration
        objv = oo.get_objective(spec)
        self.assertEqual(objv.doc, doc)
        self.assertEqual(objv.weight, oww)
        self.assertEqual(objv.model_names, mnm)
        nptest.assert_array_equal(objv.model_weights, mww, verbose=True)
        self.assertEqual(objv.ref_data, ref)
        self.assertEqual(objv.subweights, subw)
        self.assertEqual(objv.query_key, 'Etot')
        self.assertEqual(objv.objtype, 'weighted_sum')
        dat = [20, 12, 16]
        database.update('SiO2-quartz/scc', {'Etot': dat[0]})
        database.update('Si/scc', {'Etot': dat[1]})
        database.update('O2/scc', {'Etot': dat[2]})
        # check __call__()
        mdat, rdat, weights = objv.get(database)
        nptest.assert_array_equal(mdat, np.dot(np.asarray(dat), np.asarray(mww)), verbose=True)
        nptest.assert_array_equal(rdat, ref, verbose=True)
        nptest.assert_array_equal(weights, subw, verbose=True)

    def test_objtype_bands(self):
        """Can we create objective from spec for bands?"""
        yamldata = """objectives:
            - bands: 
                doc: Valence Band, Si
                models: Si/bs
                ref: 
                    file: ./reference_data/fakebands.dat 
                    loader_args: {unpack: True}
                    process:       # eliminate unused columns, like k-pt enumeration
                        # indexes and ranges below refer to file, not array, 
                        # i.e. independent of 'unpack' loader argument
                        rm_columns: 1                # filter k-point enumeration, and bands, potentially
                        # rm_rows   : [[18,36], [1,4]] # filter k-points if needed for some reason
                        # scale     : 1                # for unit conversion, e.g. Hartree to eV, if needed
                options:
                    use_ref: [[2, 4]]                # fortran-style index-bounds of bands to use
                    use_model: [[1, 3]]              # model has lesser number of bands
                    # Alignment works after data has been masked by use_* clause, and therefore
                    # the indexes below do not correspond to original but masked array
                    align_ref: [3, max]              # fortran-style index of band and k-point,
                    align_model: [3, max]            # or a function (e.g. min, max) instead of k-point
                    normalise: false
                    subweights: 
                        # NOTABENE:
                        # --------------------------------------------------
                        # Energy values are with respect to the ALIGNEMENT.
                        # If we want to have the reference  band index as zero,
                        # we would have to do tricks with the range specification 
                        # behind the curtain, to allow both positive and negative 
                        # band indexes, e.g. [-3, 0], INCLUSIVE of either boundary.
                        # Currently this is not done, so only standard Fortran
                        # range spec is supported. Therefore, band 1 is always
                        # the lowest lying, and e.g. band 4 is the third above it.
                        # --------------------------------------------------
                        dflt: 1
                        values: # [[range], subweight] for E-k points in the given range of energy
                        # notabene: the range below is with respect to the alignment value
                            - [[-0.2, 0.], 3.5]
                        bands: # [[range], subweight] of bands indexes; fortran-style
                            - [[2, 3], 1.5]   # two valence bands below the top VB
                            - [4 , 3.0]       # emphasize the reference band
                        # not supported yet     ipoint:
                weight: 1.0
            """
        spec = yaml.load(yamldata)['objectives'][0]
        que  = 'bands'
        doc  = spec[que]['doc']
        model  = 'Si/bs'
        mww = [1]
        oww  = 1
        ref  = np.loadtxt('reference_data/fakebands.dat', unpack=True)
        ref  = ref[2:5] # remove 1st col of file(k-pt enum.), consider first 3 bands from 2nd
        shift = -0.4 # this is the top of the VB (cf: fakebands.dat)
        ref -= shift
        shape = ref.shape
        # we have use_model => only a subset of bands is needed
        subset_ind = np.array([0,1,2])
        # subweights
        subw  = np.ones(shape)
        subw[1:2] = 1.5
        subw[2] = 3.0
        # subweights on value are the last one to be applied
        subw[ref > -0.2] = 3.5
        subw = subw/np.sum(subw)
        database = Database()
#        # check declaration
        objv = oo.get_objective(spec)
        self.assertEqual(objv.doc, doc)
        self.assertEqual(objv.query_key, que)
        self.assertEqual(objv.weight, oww)
        self.assertEqual(objv.model_names, model)
        nptest.assert_array_equal(objv.model_weights, mww)
        nptest.assert_array_equal(objv.ref_data, ref, verbose=True)
        nptest.assert_array_equal(objv.subset_ind, subset_ind, verbose=True)
        nptest.assert_array_equal(objv.subweights, subw, verbose=True)
        # check the __call__()
        data = np.loadtxt("reference_data/fakebands-2.dat", unpack=True)
        database.update('Si/bs', {'bands': data[1:]})
        mdat, rdat, weights = objv.get(database)
        nptest.assert_array_almost_equal(mdat, ref, decimal=2, verbose=True)
        nptest.assert_array_equal(rdat, ref, verbose=True)
        nptest.assert_array_equal(weights, subw, verbose=True)


class SetObjectivesTest(unittest.TestCase):
    """Check if we can create objectives from skpar_in.yaml"""

    def test_setobjectives(self):
        """Can we create a number of objectives from input spec?"""
        with open("test_objectives.yaml", 'r') as ff:
            try:
                spec = yaml.load(ff)['objectives']
            except yaml.YAMLError as exc:
                logger.debug (exc)
        objectives = oo.set_objectives(spec)
        for objv in objectives:
            #logger.debug ()
            logger.debug (objv)


class EvaluateObjectivesTest(unittest.TestCase):
    """Check if we can evaluate the fitness of each objective"""

    def test_evaluate_singleitem(self):
        """Can we evaluate value-type objective for a single model"""
        yamldata = """objectives:
            - item:
                models: A
                ref: 1.0
        """
        # set data base
        database = Database()
        database.update('A')
        db = database.get('A')
        # declaration of objective
        spec = yaml.load(yamldata)['objectives'][0]
        objv = oo.get_objective(spec)
        # evaluate
        db['item'] = 1.2
        self.assertAlmostEqual(0.2, objv(database))

    def test_evaluate_multiplemodels_singleitem(self):
        """Can we evaluate value-type objective for multiple models"""
        yamldata = """objectives:
            - item:
                models: [A, B, C]
                ref: [2.0, 2., 3.]
                options:
                    # normalise: True
                    subweights: [2, 1, 1.5]
        """
        # set model data
        database = Database()
        db1 = {'item': 1.0}
        db2 = {'item': 1.0}
        db3 = {'item': 1.0}
        database.update('A', db1)
        _db = database.get('A')
        self.assertDictEqual(_db, db1)
        database.update('B', db2)
        database.update('C', db3)
        # declaration of objective
        spec = yaml.load(yamldata)['objectives'][0]
        objv = oo.get_objective(spec)
        # evaluate
        self.assertAlmostEqual(1.4142135623730951, objv(database))

    def test_evaluate_bands(self):
        """Can we evaluate value-type objective of type bands (2D array)"""
        yamldata = """objectives:
            - bands: 
                models: A
                ref: 
                    file: ./reference_data/fakebands.dat
                    loader_args: {unpack: False}
                    process:
                        rm_columns: 1
                eval: [RMS, relerr]
        """
        # set model data
        database = Database()
        database.update('A')
        db1 = database.get('A')
        # declaration of objective
        spec = yaml.load(yamldata)['objectives'][0]
        objv = oo.get_objective(spec)
        self.assertAlmostEqual(1., np.sum(objv.subweights))
        #logger.debug(objv.ref_data)
        #logger.debug(objv.subweights)
        db1['bands'] = objv.ref_data * 1.1
        cost = np.sqrt(np.sum(objv.subweights*relerr(objv.ref_data, db1['bands'])**2))
        #logger.debug(cost)
        # evaluate
        self.assertAlmostEqual(cost, objv(database))


if __name__ == '__main__':
    unittest.main()

