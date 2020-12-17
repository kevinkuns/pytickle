"""
Unit tests for optickle PDH frequency response and sweeps
"""

import matlab.engine
import numpy as np
import pytickle.optickle as pyt
import pytickle.plant as plant
import os
import close
import pytest

eng = matlab.engine.start_matlab()
pyt.addOpticklePath(eng)


fmod = 11e3
gmod = 0.1
vRF = np.array([-fmod, 0, fmod])
Pin = 1
Ti = 0.01
Lcav = 40e3

data = np.load('data/optickle_PDH_data.npz')


def optFP(opt_name):
    opt = pyt.PyTickle(eng, opt_name, vRF)

    opt.addMirror('IX', Thr=Ti)
    opt.addMirror('EX', Thr=0)
    opt.addLink('IX', 'fr', 'EX', 'fr', Lcav)
    opt.addLink('EX', 'fr', 'IX', 'fr', Lcav)
    opt.setCavityBasis('EX', 'IX')

    for optic in ['IX', 'EX']:
        opt.setMechTF(optic, [], [0, 0], 1)

    opt.addSource('Laser', np.sqrt(Pin)*(vRF == 0))
    opt.addModulator('AM', 1)
    opt.addModulator('PM', 1j)
    opt.addRFmodulator('Mod', fmod, gmod*1j)
    opt.addLink('Laser', 'out', 'AM', 'in', 0)
    opt.addLink('AM', 'out', 'PM', 'in', 0)
    opt.addLink('PM', 'out', 'Mod', 'in', 0)
    opt.addLink('Mod', 'out', 'IX', 'bk', 0)

    opt.addSink('REFL')
    opt.addLink('IX', 'bk', 'REFL', 'in', 0)
    opt.addReadout('REFL', fmod, 0)

    return opt


class TestFreqResp:

    opt = optFP('optFR')
    ff = np.logspace(-2, 4, 1000)
    opt.run(ff)
    opt.save('test_PDH.hdf5')
    opt2 = plant.OpticklePlant()
    opt2.load('test_PDH.hdf5')
    os.remove('test_PDH.hdf5')

    def test_tfI(self):
        tfI = self.opt.getTF('REFL_I', 'EX')
        assert close.allclose(tfI, data['tfI'])

    def test_tfQ(self):
        tfQ = self.opt.getTF('REFL_Q', 'EX')
        assert close.allclose(tfQ, data['tfQ'])

    def test_qnI(self):
        qnI = self.opt.getQuantumNoise('REFL_I')
        assert close.allclose(qnI, data['qnI'])

    def test_qnQ(self):
        qnQ = self.opt.getQuantumNoise('REFL_Q')
        assert close.allclose(qnQ, data['qnQ'])

    def test_qnDC(self):
        qnDC = self.opt.getQuantumNoise('REFL_DC')
        assert close.allclose(qnDC, data['qnDC'])

    def test_phaseI(self):
        tf = self.opt.getTF('REFL_I', 'PM', dof='drive')
        assert close.allclose(tf, data['tfI_phase'])

    def test_phaseQ(self):
        tf = self.opt.getTF('REFL_Q', 'PM', dof='drive')
        assert close.allclose(tf, data['tfQ_phase'])

    def test_ampI(self):
        tf = self.opt.getTF('REFL_I', 'AM', dof='drive')
        assert close.allclose(tf, data['tfI_amp'])

    def test_ampQ(self):
        tf = self.opt.getTF('REFL_Q', 'AM', dof='drive')
        assert close.allclose(tf, data['tfQ_amp'])

    def test_DC_DC(self):
        sig = self.opt.getSigDC('REFL_DC')
        assert close.isclose(sig, data['dcDC'])

    def test_DC_I(self):
        sig = self.opt.getSigDC('REFL_I')
        assert close.isclose(sig, data['dcI'])

    def test_DC_Q(self):
        sig = self.opt.getSigDC('REFL_Q')
        assert close.isclose(sig, data['dcQ'])

    def test_reload_tfI(self):
        tfI = self.opt2.getTF('REFL_I', 'EX')
        assert close.allclose(tfI, data['tfI'])

    def test_reload_tfQ(self):
        tfQ = self.opt2.getTF('REFL_Q', 'EX')
        assert close.allclose(tfQ, data['tfQ'])

    def test_reload_qnI(self):
        qnI = self.opt2.getQuantumNoise('REFL_I')
        assert close.allclose(qnI, data['qnI'])

    def test_reload_qnQ(self):
        qnQ = self.opt2.getQuantumNoise('REFL_Q')
        assert close.allclose(qnQ, data['qnQ'])

    def test_reload_qnDC(self):
        qnDC = self.opt2.getQuantumNoise('REFL_DC')
        assert close.allclose(qnDC, data['qnDC'])

    def test_reload_phaseI(self):
        tf = self.opt2.getTF('REFL_I', 'PM', dof='drive')
        assert close.allclose(tf, data['tfI_phase'])

    def test_reload_phaseQ(self):
        tf = self.opt2.getTF('REFL_Q', 'PM', dof='drive')
        assert close.allclose(tf, data['tfQ_phase'])

    def test_reload_ampI(self):
        tf = self.opt2.getTF('REFL_I', 'AM', dof='drive')
        assert close.allclose(tf, data['tfI_amp'])

    def test_reload_ampQ(self):
        tf = self.opt2.getTF('REFL_Q', 'AM', dof='drive')
        assert close.allclose(tf, data['tfQ_amp'])

    def test_reload_DC_DC(self):
        sig = self.opt2.getSigDC('REFL_DC')
        assert close.isclose(sig, data['dcDC'])

    def test_reload_DC_I(self):
        sig = self.opt2.getSigDC('REFL_I')
        assert close.isclose(sig, data['dcI'])

    def test_reload_DC_Q(self):
        sig = self.opt2.getSigDC('REFL_Q')
        assert close.isclose(sig, data['dcQ'])


class TestSweep:

    opt = optFP('optSweep')
    ePos = {'EX': 5e-9}
    sPos = {k: -v for k, v in ePos.items()}
    opt.sweepLinear(sPos, ePos, 1000)

    def test_sweepI(self):
        poses, sweepI = self.opt.getSweepSignal('REFL_I', 'EX')
        assert close.allclose(sweepI, data['sweepI'])

    def test_sweepQ(self):
        poses, sweepQ = self.opt.getSweepSignal('REFL_Q', 'EX')
        assert close.allclose(sweepQ, data['sweepQ'])
