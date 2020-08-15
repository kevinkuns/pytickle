"""
Unit tests for finesse torsional spring
"""

import numpy as np
import pytickle.finesse as fin
import pytickle.controls as ctrl
import pytickle.plant as plant
import pykat
import os
import pytest

data = np.load('data/finesse_TorsionalSpring_data.npz')

fmod = 11e3
gmod = 0.1
Pin = 10e3
Ti = 0.014
Lcav = 40e3
Ri = 34e3
Re = 36e3

gi = 1 - Lcav/Ri
ge = 1 - Lcav/Re
r = 2/((gi - ge) + np.sqrt((gi - ge)**2 + 4))

I = 25
f0 = 1
Q = 100
poles = np.array(ctrl.resRoots(2*np.pi*f0, Q, Hz=False))

kat = pykat.finesse.kat()

# make the cavity
fin.addMirror(kat, 'EX', Chr=1/Re)
fin.addMirror(kat, 'IX', Thr=Ti, Chr=1/Ri)
fin.addSpace(kat, 'IX_fr', 'EX_fr', Lcav)
fin.setCavityBasis(kat, 'IX_fr', 'EX_fr')

# set the pitch response
fin.setMechTF(kat, 'EX', [], poles, 1/I, doftype='pitch')
fin.setMechTF(kat, 'IX', [], poles, 1/I, doftype='pitch')

# add input
fin.addLaser(kat, 'Laser', Pin)
fin.addModulator(kat, 'Mod', fmod, gmod, 1, 'pm')
fin.addSpace(kat, 'Laser_out', 'Mod_in', 0)
fin.addSpace(kat, 'Mod_out', 'IX_bk', 0)

# add DC and RF photodiodes
fin.addReadout(kat, 'REFL', 'IX_bk', fmod, 0, doftype='pitch')

fin.monitorMotion(kat, 'EX', doftype='pitch')
fin.monitorMotion(kat, 'IX', doftype='pitch')

fin.monitorBeamSpotMotion(kat, 'EX_fr')
fin.monitorBeamSpotMotion(kat, 'IX_fr')

kat.phase = 2
kat.maxtem = 1

katTF = fin.KatFR(kat)

HARD = {'IX': -1, 'EX': r}
SOFT = {'IX': r, 'EX': 1}

fmin = 1e-1
fmax = 30
npts = 1000
katTF.run(fmin, fmax, npts, doftype='pitch')
katTF.runDC()

katTF.save('test_torsional_spring.hdf5')
katTF2 = plant.FinessePlant()
katTF2.load('test_torsional_spring.hdf5')
os.remove('test_torsional_spring.hdf5')

def test_REFLI_HARD():
    hard = ctrl.DegreeOfFreedom(HARD, 'pitch')
    tf1 = katTF.getTF('REFL_I', HARD, doftype='pitch')
    tf2 = katTF.getTF('REFL_I', hard)
    ref = data['tf_REFLI_HARD']
    c1 = np.allclose(tf1, ref)
    c2 = np.allclose(tf2, ref)
    assert np.all([c1, c2])


def test_REFLI_SOFT():
    tf = katTF.getTF('REFL_I', SOFT, doftype='pitch')
    ref = data['tf_REFLI_SOFT']
    assert np.allclose(tf, ref)


def test_mech_HARD():
    tf = katTF.getMechTF(HARD, HARD, doftype='pitch')
    ref = data['mech_HARD']
    assert np.allclose(tf, ref)


def test_mech_SOFT():
    tf = katTF.getMechTF(SOFT, SOFT, doftype='pitch')
    ref = data['mech_SOFT']
    assert np.allclose(tf, ref)


def test_mMech_EX_EX():
    mMech = katTF.getMechMod('EX', 'EX', doftype='pitch')
    ref = data['mMech_EX_EX']
    assert np.allclose(mMech, ref)


def test_mMech_EX_EX2():
    ex = ctrl.DegreeOfFreedom('EX', doftype='pitch')
    mMech1 = katTF.getMechMod('EX', ex, doftype='pitch')
    mMech2 = katTF.getMechMod(ex, 'EX', doftype='pitch')
    ref = data['mMech_EX_EX']
    c1 = np.allclose(mMech1, ref)
    c2 = np.allclose(mMech2, ref)
    assert np.all([c1, c2])


def test_mMech_IX_EX():
    mMech = katTF.getMechMod('IX', 'EX', doftype='pitch')
    ref = data['mMech_IX_EX']
    assert np.allclose(mMech, ref)


def test_mMech_IX_EX2():
    ex = ctrl.DegreeOfFreedom('EX', 'pitch')
    ix = ctrl.DegreeOfFreedom('IX', 'pitch')
    mMech = katTF.getMechMod(ix, ex)
    ref = data['mMech_IX_EX']
    assert np.allclose(mMech, ref)


def test_bsm_EX_IX():
    bsm = katTF.computeBeamSpotMotion('EX_fr', 'IX', 'pitch')
    ref = data['bsm_EX_IX']
    assert np.allclose(bsm, ref)


def test_bsm_EX_EX():
    bsm = katTF.computeBeamSpotMotion('EX_fr', 'EX', 'pitch')
    ref = data['bsm_EX_EX']
    assert np.allclose(bsm, ref)


##############################################################################
# test reloaded plants
##############################################################################

def test_load_REFLI_HARD():
    tf = katTF2.getTF('REFL_I', HARD, doftype='pitch')
    ref = data['tf_REFLI_HARD']
    assert np.allclose(tf, ref)


def test_load_REFLI_SOFT():
    tf = katTF2.getTF('REFL_I', SOFT, doftype='pitch')
    ref = data['tf_REFLI_SOFT']
    assert np.allclose(tf, ref)


def test_load_mech_HARD():
    tf = katTF2.getMechTF(HARD, HARD, doftype='pitch')
    ref = data['mech_HARD']
    assert np.allclose(tf, ref)


def test_load_mech_SOFT():
    tf = katTF2.getMechTF(SOFT, SOFT, doftype='pitch')
    ref = data['mech_SOFT']
    assert np.allclose(tf, ref)


def test_load_mMech_EX_EX():
    mMech = katTF2.getMechMod('EX', 'EX', doftype='pitch')
    ref = data['mMech_EX_EX']
    assert np.allclose(mMech, ref)


def test_load_mMech_IX_EX():
    mMech = katTF2.getMechMod('IX', 'EX', doftype='pitch')
    ref = data['mMech_IX_EX']
    assert np.allclose(mMech, ref)


def test_load_bsm_EX_IX():
    bsm = katTF2.computeBeamSpotMotion('EX_fr', 'IX', 'pitch')
    ref = data['bsm_EX_IX']
    assert np.allclose(bsm, ref)


def test_load_bsm_EX_EX():
    bsm = katTF2.computeBeamSpotMotion('EX_fr', 'EX', 'pitch')
    ref = data['bsm_EX_EX']
    assert np.allclose(bsm, ref)
