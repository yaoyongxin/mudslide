#!/usr/bin/env python

## @package models
#  Implementations of the one-dimensional two-state models Tully demonstrated FSSH on in Tully, J.C. <I>J. Chem. Phys.</I> 1990 <B>93</B> 1061.

import numpy as np
from scipy.special import erf

from .electronics import DiabaticModel_, AdiabaticModel_

# Here are some helper functions that pad the model problems with fake electronic states.
# Useful for debugging, so keeping it around
'''
def pad_model(nstates, diags):
    def V_decorator(func):
        def wrapper(*args, **kwargs):
            out = func(*args, **kwargs)
            oldnstates = out.shape[0]
            out = np.pad(out, (0,nstates), 'constant')
            if nstates > 1:
                for i in range(nstates):
                    out[oldnstates+i,oldnstates+i] = diags[i]
            else:
                out[-1,-1] = diags
            return out
        return wrapper

    def dV_decorator(func):
        def wrapper(*args, **kwargs):
            out = func(*args, **kwargs)
            nout = np.zeros([out.shape[0], out.shape[1]+nstates, out.shape[2]+nstates])
            nout[:,0:out.shape[1],0:out.shape[2]] += out[:,:,:]
            return nout
        return wrapper

    def nstates_decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs) + nstates
        return wrapper

    def class_decorator(cls):
        class padded_model(cls):
            def __init__(self, *args, **kwargs):
                cls.__init__(self, *args, **kwargs)

                self.V = V_decorator(self.V)
                self.dV = dV_decorator(self.dV)
                self.nstates = nstates_decorator(self.nstates)

        return padded_model
    return class_decorator
'''

## Tunneling through a single barrier model used in Tully's 1990 JCP
#
# \f[
#     V_{11} = \left\{ \begin{array}{cr}
#                   A (1 - e^{Bx}) & x < 0 \\
#                  -A (1 - e^{-Bx}) & x > 0
#                   \end{array} \right.
# \f]
# \f[ V_{22} = -V_{11} \f]
# \f[ V_{12} = V_{21} = C e^{-D x^2} \f]
class TullySimpleAvoidedCrossing(DiabaticModel_):
    ndim_ = 1
    nstates_ = 2

    ## Constructor that defaults to the values reported in Tully's 1990 JCP
    def __init__(self, representation="adiabatic", reference=None,
            a = 0.01, b = 1.6, c = 0.005, d = 1.0, mass = 2000.0):
        DiabaticModel_.__init__(self, representation=representation, reference=reference)

        self.A = a
        self.B = b
        self.C = c
        self.D = d
        self.mass = np.array(mass, dtype=np.float64).reshape(self.ndim())

    ## \f$V(x)\f$
    def V(self, x):
        v11 = float(np.copysign(self.A, x) * ( 1.0 - np.exp(-self.B * np.abs(x)) ))
        v22 = -v11
        v12 = float(self.C * np.exp(-self.D * x * x))
        out = np.array([ [v11, v12], [v12, v22] ], dtype=np.float64)
        return out

    ## \f$\nabla V(x)\f$
    def dV(self, x):
        xx = np.array(x, dtype=np.float64)
        v11 = self.A * self.B * np.exp(-self.B * abs(xx))
        v22 = -v11
        v12 = -2.0 * self.C * self.D * xx * np.exp(-self.D * xx * xx)
        out = np.array([ [v11, v12],
                         [v12, v22] ], dtype=np.float64)
        return out.reshape([1, 2, 2])

## Tunneling through a double avoided crossing used in Tully's 1990 JCP
#
# \f[ V_{11} = 0 \f]
# \f[ V_{22} = -A e^{-Bx^2} + E_0 \f]
# \f[ V_{12} = V_{21} = C e^{-D x^2} \f]
class TullyDualAvoidedCrossing(DiabaticModel_):
    ndim_ = 1
    nstates_ = 2

    ## Constructor that defaults to the values reported in Tully's 1990 JCP
    def __init__(self, representation="adiabatic", reference=None,
            a = 0.1, b = 0.28, c = 0.015, d = 0.06, e = 0.05, mass = 2000.0):
        DiabaticModel_.__init__(self, representation=representation, reference=reference)
        self.A = a
        self.B = b
        self.C = c
        self.D = d
        self.E0 = e
        self.mass = np.array(mass, dtype=np.float64).reshape(self.ndim())

    ## \f$V(x)\f$
    def V(self, x):
        v11 = 0.0
        v22 = float(-self.A * np.exp(-self.B * x * x) + self.E0)
        v12 = float(self.C * np.exp(-self.D * x * x))
        out = np.array([ [v11, v12],
                         [v12, v22] ], dtype=np.float64)
        return out

    ## \f$\nabla V(x)\f$
    def dV(self, x):
        xx = np.array(x, dtype=np.float64)
        v11 = np.zeros_like(xx)
        v22 = 2.0 * self.A * self.B * xx * np.exp(-self.B * xx * xx)
        v12 = -2.0 * self.C * self.D * xx * np.exp(-self.D * xx * xx)
        out = np.array([ [v11, v12],
                         [v12, v22] ], dtype=np.float64)
        return out.reshape([1, 2, 2])

## Model with extended coupling and the possibility of reflection. The most challenging of the
#  models used in Tully's 1990 JCP
# \f[ V_{11} = A \f]
# \f[ V_{22} = -A \f]
# \f[
#     V_{12} = \left\{ \begin{array}{cr}
#                   B e^{Cx} & x < 0 \\
#                   B \left( 2 - e^{-Cx} \right) & x > 0
#                   \end{array} \right.
# \f]
class TullyExtendedCouplingReflection(DiabaticModel_):
    ndim_ = 1
    nstates_ = 2

    ## Constructor that defaults to the values reported in Tully's 1990 JCP
    def __init__(self, representation="adiabatic", reference=None,
            a = 0.0006, b = 0.10, c = 0.90, mass = 2000.0):
        DiabaticModel_.__init__(self, representation=representation, reference=reference)
        self.A = a
        self.B = b
        self.C = c
        self.mass = np.array(mass, dtype=np.float64).reshape(self.ndim())

    ## \f$V(x)\f$
    def V(self, x):
        v11 = self.A
        v22 = -self.A
        v12 = float(np.exp(-np.abs(x)*self.C))
        if x < 0:
            v12 = self.B * v12
        else:
            v12 = self.B * (2.0 - v12)
        out = np.array([ [v11, v12],
                         [v12, v22] ], dtype=np.float64)
        return out

    ## \f$\nabla V(x)\f$
    def dV(self, x):
        xx = np.array(x, dtype=np.float64)
        v11 = np.zeros_like(xx)
        v22 = np.zeros_like(xx)
        v12 = self.B * self.C * np.exp(-self.C * np.abs(xx))
        out = np.array([ [v11, v12],
                         [v12, v22] ], dtype=np.float64)
        return out.reshape([1, 2, 2])

class SuperExchange(DiabaticModel_):
    nstates_ = 3
    ndim_ = 1

    ## Constructor defaults to Prezhdo paper on GFSH
    def __init__(self, representation="adiabatic", reference=None,
            v11 = 0.0, v22 = 0.01, v33 = 0.005, v12 = 0.001, v23 = 0.01, mass = 2000.0):
        DiabaticModel_.__init__(self, representation=representation, reference=reference)
        self.v11 = v11
        self.v22 = v22
        self.v33 = v33
        self.v12 = v12
        self.v23 = v23
        self.mass = np.array(mass, dtype=np.float64).reshape(self.ndim())

    ## \f$V(x)\f$
    def V(self, x):
        v12 = self.v12 * np.exp(-0.5*x*x)
        v23 = self.v23 * np.exp(-0.5*x*x)

        return np.array([ [self.v11, v12, 0.0],
                          [v12, self.v22, v23],
                          [0.0, v23, self.v33] ], dtype=np.float64)

    ## \f$ \nabla V(x)\f$
    def dV(self, x):
        v12 = -x * self.v12 * np.exp(-0.5*x*x)
        v23 = -x * self.v23 * np.exp(-0.5*x*x)
        out = np.array([ [0.0, v12, 0.0],
                         [v12, 0.0, v23],
                         [0.0, v23, 0.0] ], dtype=np.float64)

        return out.reshape([1, 3, 3])

class SubotnikModelX(DiabaticModel_):
    nstates_ = 3
    ndim_ = 1

    ## Constructor defaults to Subotnik JPCA 2011 paper on decoherence
    def __init__(self, representation="adiabatic", reference=None,
            a = 0.03, b=1.6, c=0.005, xp=7.0, mass=2000.0):
        DiabaticModel_.__init__(self, representation=representation, reference=reference)
        self.a = float(a)
        self.b = float(b)
        self.c = float(c)
        self.xp = float(xp)
        self.mass = np.array(mass, dtype=np.float64).reshape(self.ndim())

    ## \f$V(x)\f$
    def V(self, x):
        xx = np.array( [ x - self.xp, x, x + self.xp ] )
        tan = self.a * np.tanh(self.b * xx)
        ex = self.c * np.exp(-xx**2)

        v11 = tan[1] + tan[2]
        v22 = -(tan[0] + tan[1])
        v33 = -(tan[2] - tan[0])
        v12 = ex[1]
        v13 = ex[2]
        v23 = ex[0]

        return np.array([ [v11, v12, v13],
                          [v12, v22, v23],
                          [v13, v23, v33] ], dtype=np.float64)

    ## \f$ \nabla V(x)\f$
    def dV(self, x):
        xx = np.array( [ x - self.xp, x, x + self.xp ] )
        tan = self.a * self.b * np.cosh(self.b * xx)**(-2)
        ex = -2.0 * xx * self.c * np.exp(-xx**2)

        v11 = tan[1] + tan[2]
        v22 = -(tan[0] + tan[1])
        v33 = -(tan[2] - tan[0])
        v12 = ex[1]
        v13 = ex[2]
        v23 = ex[0]

        out =  np.array([ [v11, v12, v13],
                          [v12, v22, v23],
                          [v13, v23, v33] ], dtype=np.float64)

        return out.reshape([1, 3, 3])

class SubotnikModelS(DiabaticModel_):
    nstates_ = 3
    ndim_ = 1

    ## Constructor defaults to Subotnik JPCA 2011 paper on decoherence
    def __init__(self, representation="adiabatic", reference=None,
            a = 0.015, b=1.0, c=0.005, d=0.5, xp=7.0, mass=2000.0):
        DiabaticModel_.__init__(self, representation=representation, reference=reference)
        self.a = float(a)
        self.b = float(b)
        self.c = float(c)
        self.d = float(d)
        self.xp = float(xp)
        self.mass = np.array(mass, dtype=np.float64).reshape(self.ndim())

    ## \f$V(x)\f$
    def V(self, x):
        xx = np.array( [ x - self.xp, x, x + self.xp ] )
        tan = self.a * np.tanh(self.b * xx)
        ex = self.c * np.exp(-xx**2)

        v11 = tan[0] - tan[2] + self.a
        v22 = -(tan[0] - tan[2]) - self.a
        v33 = 2.0 * self.a * np.tanh(self.d * x)
        v12 = ex[2] + ex[0]
        v13 = ex[1]
        v23 = ex[1]

        return np.array([ [v11, v12, v13],
                          [v12, v22, v23],
                          [v13, v23, v33] ], dtype=np.float64)

    ## \f$ \nabla V(x)\f$
    def dV(self, x):
        xx = np.array( [ x - self.xp, x, x + self.xp ] )
        tan = self.a * self.b * np.cosh(self.b * xx)**(-2)
        ex = -2.0 * xx * self.c * np.exp(-xx**2)

        v11 = tan[0] - tan[2]
        v22 = -(tan[0] - tan[2])
        v33 = 2 * self.a * self.d * np.cosh(self.d * x)**(-2)
        v12 = ex[2] + ex[0]
        v13 = ex[1]
        v23 = ex[1]

        out =  np.array([ [v11, v12, v13],
                          [v12, v22, v23],
                          [v13, v23, v33] ], dtype=np.float64)

        return out.reshape([1, 3, 3])

class Subotnik2D(DiabaticModel_):
    nstates_ = 2
    ndim_ = 2

    ## Constructor defaults to Subotnik JPCA 2011 paper on decoherence
    def __init__(self, representation="adiabatic", reference=None,
            a=0.2, b=0.6, c=0.015, d=0.3, f=0.05, g=0.3, w=2.0, mass=2000.0):
        DiabaticModel_.__init__(self, representation=representation, reference=reference)
        self.a = float(a)
        self.b = float(b)
        self.c = float(c)
        self.d = float(d)
        self.f = float(f)
        self.g = float(g)
        self.w = float(w)
        self.mass = np.array(mass, dtype=np.float64).reshape(self.ndim())

    ## \f$V(x)\f$
    def V(self, r):
        x, y = r[0], r[1]
        v11 = -self.f * np.tanh(self.b * x)
        z = self.b * (x - 1.0) + self.w * np.cos(self.g * y + np.pi * 0.5)
        v22 = self.a * np.tanh(z) + 0.75 * self.a
        v12 = self.c * np.exp(- self.d * x * x)

        return np.array([ [v11, v12],
                          [v12, v22] ], dtype=np.float64)

    ## \f$ \nabla V(x)\f$
    def dV(self, r):
        x, y = r[0], r[1]

        z = self.b * (x - 1.0) + self.w * np.cos(self.G * y + np.pi * 0.5)

        v11x = -self.f * self.b * self.cosh(self.b * x)**(-2)
        zx = self.b
        v22x = self.a * zx * np.cosh(z)**(-2)
        v12x = - 2.0 * self.d * self.x * self.c * np.exp(-self.d * x * x)

        v11y = 0.0
        zy = -self.w * self.g * np.sin(self.g * y + np.pi * 0.5)
        v22y = self.a * zy * np.cosh(z)**(-2)
        v12y = 0.0

        vx = [ [v11x, v12x], [v12x, v22x] ]
        vy = [ [v11y, v12y], [v12y, v22y] ]

        out =  np.array([ vx, vy ], dtype=np.float64)

        return out.reshape([2, 3, 3])

class ShinMetiu(AdiabaticModel_):
    ## Constructor defaults to classic Shin-Metiu as described in
    ## Gossel, Liacombe, Maitra JCP 2019
    ndim_ = 1

    def __init__(self, representation="adiabatic", reference=None, nstates = 3, L = 19.0, Rf = 5.0, Rl = 3.1, Rr = 4.0, mass = 1836.0,
            m_el = 1.0, nel = 128, box = None):
        AdiabaticModel_.__init__(self, representation=representation, reference=reference)

        self.L = L
        self.ion_left = -self.L*0.5
        self.ion_right = self.L*0.5
        self.Rf = Rf
        self.Rl = Rl
        self.Rr = Rr
        self.mass = np.array(mass, dtype=np.float64).reshape(self.ndim())
        self.m_el = m_el

        if box is None:
            box = L
        box_left, box_right = -0.5 * box, 0.5 * box
        self.rr = np.linspace(box_left + 1e-12, box_right - 1e-12, nel, endpoint=True,
                dtype=np.float64)

        self.nstates_ = nstates

    def soft_coulomb(self, r12, gamma):
        abs_r12 = np.abs(r12)
        return erf(abs_r12/gamma)/abs_r12

    def d_soft_coulomb(self, r12, gamma):
        abs_r12 = np.abs(r12)
        two_over_root_pi = 2.0 / np.sqrt(np.pi)
        out = r12 * erf(abs_r12/gamma) / (abs_r12**3) \
                - two_over_root_pi * r12 * np.exp(-abs_r12**2/(gamma**2)) / (gamma * abs_r12 * abs_r12)
        return out

    def V_nuc(self, R):
        v0 = 1.0/np.abs(R - self.ion_left) + 1.0/np.abs(R - self.ion_right)
        return v0

    def V_el(self, R):
        rr = self.rr

        v_en = -self.soft_coulomb(rr-R, self.Rf)
        v_le = -self.soft_coulomb(rr-self.ion_left, self.Rl)
        v_re = -self.soft_coulomb(rr-self.ion_right, self.Rr)
        vv = v_en + v_le + v_re

        nr = len(rr)
        dr = rr[1] - rr[0]

        T = (-0.5/(self.m_el * dr * dr)) * (np.eye(nr, k=-1, dtype=np.float64)
                - 2.0*np.eye(nr, dtype=np.float64) + np.eye(nr,k=1, dtype=np.float64))
        H = T + np.diag(vv)

        return H

    def dV_nuc(self, R):
        LmR = np.abs(0.5 * self.L - R)
        LpR = np.abs(0.5 * self.L + R)
        dv0 = LmR / np.abs(LmR**3) - LpR / np.abs(LpR**3)

        return dv0

    def dV_el(self, R):
        rr = self.rr
        rR = R - rr
        dvv = self.d_soft_coulomb(rR, self.Rf)
        return np.diag(dvv)

    ## \f$V(x)\f$
    def V(self, R):
        return self.V_el(R) + self.V_nuc(R)

    ## \f$\frac{V(x)}{dR}\f$
    def dV(self, R):
        return (self.dV_el(R) + self.dV_nuc(R)).reshape([1, len(self.rr), len(self.rr)])


models =    { "simple" : TullySimpleAvoidedCrossing,
              "dual"   : TullyDualAvoidedCrossing,
              "extended" : TullyExtendedCouplingReflection,
              "super"  : SuperExchange,
              "shin-metiu" : ShinMetiu,
              "modelx" : SubotnikModelX,
              "models" : SubotnikModelS
              }
