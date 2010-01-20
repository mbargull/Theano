import scipy.sparse
from theano.sparse import *

import random
import unittest
import theano

from theano import compile
from theano import gradient
from theano import gof

from theano.sparse.basic import _is_dense, _is_sparse, _is_dense_variable, _is_sparse_variable
from theano.sparse.basic import _mtypes, _mtype_to_str
from theano.tests import unittest_tools as utt


def eval_outputs(outputs):
    return compile.function([], outputs)()[0]

class T_transpose(unittest.TestCase):
    def setUp(self):
        utt.seed_rng()

    def test_transpose_csc(self):
        sp = sparse.csc_matrix(sparse.eye(5,3))
        a = as_sparse_variable(sp)
        self.failUnless(a.data is sp)
        self.failUnless(a.data.shape == (5,3))
        self.failUnless(a.type.dtype == 'float64', a.type.dtype)
        self.failUnless(a.type.format == 'csc', a.type.format)
        ta = transpose(a)
        self.failUnless(ta.type.dtype == 'float64', ta.type.dtype)
        self.failUnless(ta.type.format == 'csr', ta.type.format)

        vta = eval_outputs([ta])
        self.failUnless(vta.shape == (3,5))
    def test_transpose_csr(self):
        a = as_sparse_variable(sparse.csr_matrix(sparse.eye(5,3)))
        self.failUnless(a.data.shape == (5,3))
        self.failUnless(a.type.dtype == 'float64')
        self.failUnless(a.type.format == 'csr')
        ta = transpose(a)
        self.failUnless(ta.type.dtype == 'float64', ta.type.dtype)
        self.failUnless(ta.type.format == 'csc', ta.type.format)

        vta = eval_outputs([ta])
        self.failUnless(vta.shape == (3,5))

class T_Add(unittest.TestCase):
    def testSS(self):
        for mtype in _mtypes:
            a = mtype(numpy.array([[1., 0], [3, 0], [0, 6]]))
            aR = as_sparse_variable(a)
            self.failUnless(aR.data is a)
            self.failUnless(_is_sparse(a))
            self.failUnless(_is_sparse_variable(aR))

            b = mtype(numpy.asarray([[0, 2.], [0, 4], [5, 0]]))
            bR = as_sparse_variable(b)
            self.failUnless(bR.data is b)
            self.failUnless(_is_sparse(b))
            self.failUnless(_is_sparse_variable(bR))

            apb = add(aR, bR)
            self.failUnless(_is_sparse_variable(apb))

            self.failUnless(apb.type.dtype == aR.type.dtype, apb.type.dtype)
            self.failUnless(apb.type.dtype == bR.type.dtype, apb.type.dtype)
            self.failUnless(apb.type.format == aR.type.format, apb.type.format)
            self.failUnless(apb.type.format == bR.type.format, apb.type.format)

            val = eval_outputs([apb])
            self.failUnless(val.shape == (3,2))
            self.failUnless(numpy.all(val.todense() == (a + b).todense()))
            self.failUnless(numpy.all(val.todense() == numpy.array([[1., 2], [3, 4], [5, 6]])))

    def testSD(self):
        for mtype in _mtypes:
            a = numpy.array([[1., 0], [3, 0], [0, 6]])
            aR = tensor.as_tensor_variable(a)
            self.failUnless(aR.data is a)
            self.failUnless(_is_dense(a))
            self.failUnless(_is_dense_variable(aR))

            b = mtype(numpy.asarray([[0, 2.], [0, 4], [5, 0]]))
            bR = as_sparse_variable(b)
            self.failUnless(bR.data is b)
            self.failUnless(_is_sparse(b))
            self.failUnless(_is_sparse_variable(bR))

            apb = add(aR, bR)
            self.failUnless(_is_dense_variable(apb))

            self.failUnless(apb.type.dtype == aR.type.dtype, apb.type.dtype)
            self.failUnless(apb.type.dtype == bR.type.dtype, apb.type.dtype)

            val = eval_outputs([apb])
            self.failUnless(val.shape == (3, 2))
            self.failUnless(numpy.all(val == (a + b)))
            self.failUnless(numpy.all(val == numpy.array([[1., 2], [3, 4], [5, 6]])))

    def testDS(self):
        for mtype in _mtypes:
            a = mtype(numpy.array([[1., 0], [3, 0], [0, 6]]))
            aR = as_sparse_variable(a)
            self.failUnless(aR.data is a)
            self.failUnless(_is_sparse(a))
            self.failUnless(_is_sparse_variable(aR))

            b = numpy.asarray([[0, 2.], [0, 4], [5, 0]])
            bR = tensor.as_tensor_variable(b)
            self.failUnless(bR.data is b)
            self.failUnless(_is_dense(b))
            self.failUnless(_is_dense_variable(bR))

            apb = add(aR, bR)
            self.failUnless(_is_dense_variable(apb))

            self.failUnless(apb.type.dtype == aR.type.dtype, apb.type.dtype)
            self.failUnless(apb.type.dtype == bR.type.dtype, apb.type.dtype)

            val = eval_outputs([apb])
            self.failUnless(val.shape == (3, 2))
            self.failUnless(numpy.all(val == (a + b)))
            self.failUnless(numpy.all(val == numpy.array([[1., 2], [3, 4], [5, 6]])))

class T_conversion(unittest.TestCase):
    def setUp(self):
        utt.seed_rng()

    def test0(self):
        a = tensor.as_tensor_variable(numpy.random.rand(5))
        s = csc_from_dense(a)
        val = eval_outputs([s])
        self.failUnless(str(val.dtype)=='float64')
        self.failUnless(val.format == 'csc')

    def test1(self):
        a = tensor.as_tensor_variable(numpy.random.rand(5))
        s = csr_from_dense(a)
        val = eval_outputs([s])
        self.failUnless(str(val.dtype)=='float64')
        self.failUnless(val.format == 'csr')

    def test2(self):
        #call dense_from_sparse
        for t in _mtypes:
            s = t((2,5))
            s = t(scipy.sparse.identity(5))
            d = dense_from_sparse(s)
            s[0,0] = 1.0
            val = eval_outputs([d])
            self.failUnless(str(val.dtype)=='float64')
            self.failUnless(numpy.all(val[0] == [1,0,0,0,0]))


import scipy.sparse as sp
class test_structureddot(unittest.TestCase):
    def setUp(self):
        utt.seed_rng()

    def test_structuredot(self):
        bsize = 2
        typenames = 'float32', 'int64', 'int8', 'int32', 'int16', 'float64', 'complex64', 'complex128'
       
        for dense_dtype in typenames:
            for sparse_dtype in typenames:
                #print >> sys.stderr, dense_dtype, sparse_dtype
                # iterate for a few different random graph patterns
                for i in range(10):
                    spmat = sp.csc_matrix((4,6), dtype=sparse_dtype)
                    for k in range(5):
                        # set non-zeros in random locations (row x, col y)
                        x = numpy.floor(numpy.random.rand()*spmat.shape[0])
                        y = numpy.floor(numpy.random.rand()*spmat.shape[1])
                        spmat[x,y] = numpy.random.rand()*10
                    spmat = sp.csc_matrix(spmat)
               
                    kerns = tensor.Tensor(broadcastable=[False],
                            dtype=sparse_dtype)('kerns')
                    images = tensor.Tensor(broadcastable=[False, False],
                            dtype=dense_dtype)('images')

                    output_dtype = theano.scalar.upcast(sparse_dtype, dense_dtype)
                    ##
                    # Test compressed-sparse column matrices ###
                    ##

                    # build symbolic theano graph
                    def buildgraphCSC(kerns,images):
                        csc = CSC(kerns, spmat.indices[:spmat.size],
                                spmat.indptr, spmat.shape)
                        assert csc.type.dtype == sparse_dtype
                        rval = structured_dot(csc, images.T)
                        assert rval.type.dtype == output_dtype
                        return rval

                    out = buildgraphCSC(kerns,images)
                    f = theano.function([kerns,images], out)

                    # compute theano outputs
                    kernvals = spmat.data[:spmat.size]
                    imvals = 1.0 + 1.0 * numpy.array(
                            numpy.arange(bsize*spmat.shape[1]).\
                            reshape(bsize,spmat.shape[1]), dtype=dense_dtype)
                    #print('dense_dtype=%s' % dense_dtype)
                    #print('sparse_dtype=%s' % sparse_dtype)
                    #print('i=%s' % i)
                    print 'kerntype', str(kernvals.dtype), kernvals.dtype.num
                    outvals = f(kernvals,imvals)
                    print 'YAY'
                    print spmat.todense()
                    print imvals.T
                    print "OUT1", outvals
                    # compare to scipy
                    c = spmat * (imvals.T)
                    assert _is_dense(c)
                    assert str(outvals.dtype) == output_dtype
                    assert numpy.all(numpy.abs(outvals - 
                        numpy.array(c, dtype=output_dtype)) < 1e-4)

                    if (sparse_dtype.startswith('float') and
                            dense_dtype.startswith('float')):
                        utt.verify_grad(buildgraphCSC, 
                                [kernvals, imvals])

                    print 'BBB'

                    ##
                    # Test compressed-sparse row matrices ###
                    ##
                    spmat = spmat.tocsr()
                    
                    # build theano graph
                    def buildgraphCSR(kerns,images):
                        csr = CSR(kerns, spmat.indices[:spmat.size], spmat.indptr, spmat.shape)
                        return structured_dot(csr, images.T)
                    out = buildgraphCSR(kerns,images)
                    f = theano.function([kerns,images], out)
                    # compute theano output
                    kernvals[:] = spmat.data[:spmat.size]
                    #kernvals = numpy.empty(spmat.size, dtype=dense_dtype)
                    imvals = 1.0 * numpy.arange(bsize*spmat.shape[1]).reshape(bsize,spmat.shape[1])
                    print 'kerntype2', str(kernvals.dtype), kernvals.dtype.num
                    outvals = f(kernvals,imvals)
                    print 'YAYAGI'
                    # compare to scipy
                    c = spmat * (imvals.T)
                    assert _is_dense(c)
                    assert str(outvals.dtype) == output_dtype
                    assert numpy.all(numpy.abs(outvals - 
                                     numpy.array(c, dtype=output_dtype)) < 1e-4)

                    # we could test more, but hopefully this suffices?
                    if sparse_dtype.startswith('float') and dense_dtype.startswith('float'):
                        utt.verify_grad( buildgraphCSR, [kernvals,imvals])

    def test_opt_unpack(self):
        kerns = tensor.Tensor(dtype='int64', broadcastable=[False])('kerns')
        spmat = sp.csc_matrix((4,6), dtype='int64')
        for i in range(5):
            # set non-zeros in random locations (row x, col y)
            x = numpy.floor(numpy.random.rand()*spmat.shape[0])
            y = numpy.floor(numpy.random.rand()*spmat.shape[1])
            spmat[x,y] = numpy.random.rand()*10
        spmat = sp.csc_matrix(spmat)
               
        images = tensor.Tensor(dtype='float32', broadcastable=[False, False])('images')

        cscmat = CSC(kerns, spmat.indices[:spmat.size], spmat.indptr, spmat.shape)
        f = theano.function([kerns, images], structured_dot(cscmat, images.T), mode='FAST_RUN')

        sdcscpresent = False
        for node in f.maker.env.toposort():
            print node.op
            assert not isinstance(node.op, CSM)
            assert not isinstance(node.op, CSMProperties)
            if isinstance(f.maker.env.toposort()[1].op, StructuredDotCSC):
                sdcscpresent = True
        assert sdcscpresent

        kernvals = numpy.array(spmat.data[:spmat.size])
        #print 'kdtype', kernvals.dtype, kernvals.shape, kernvals.ndim, kernvals.dtype.num
        #print 'type of kernvals = ', kernvals.dtype
        bsize = 3
        imvals = 1.0 * numpy.array(numpy.arange(bsize*spmat.shape[1]).\
                reshape(bsize,spmat.shape[1]), dtype='float32')
        outvals = f(kernvals,imvals)
        print outvals

if __name__ == '__main__':
    unittest.main()
