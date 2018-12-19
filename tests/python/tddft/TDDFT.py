import psi4

import numpy as np
from psi4.driver.p4util.solvers import davidson_solver
from psi4.driver.procrouting.response.scf_products import SCFProducts

mol = psi4.geometry("""
O     0.0000000000    0.0000000000    2.3054658725
H     1.7822044879    0.0000000000   -1.0289558751
H    -1.7822044879    0.0000000000   -1.0289558751
C     0.0000000000    0.0000000000    0.0000000000
symmetry c1
""")

psi4.set_options({"SAVE_JK": True})
#psi4.set_options({"e_convergence": 1.e-1, "d_convergence": 1.e-1})
# psi4.set_options({"reference": "uhf"})
e, wfn = psi4.energy("HF/6-31G", return_wfn=True)

prod = SCFProducts(wfn)

def func(vector):
    return prod.H2H1_product(vector)

def precon(resid, i, A_w):
    return resid

nvecs = 5
guess = np.ones((prod.narot, nvecs))
davidson_solver(func, precon, guess, no_eigs=nvecs, e_conv=1.e-4)
# davidson_solver(LHS_Hx_build, precon, guess, no_eigs=nvecs)


 #      Excitation              Transition Dipole Moments               Oscillator
 #       Energies            x               y               z           Strengths
 # ===============================================================================
 #      0.04153295      0.00000000     -0.00000000     -0.00000000      0.00000000
 #      0.16412863      0.03452355     -0.00000000      0.00000000      0.00013041
 #      0.29748986     -0.00000000      0.00000000     -0.77663165      0.11962201
 #      0.35309555     -0.00000000      0.00000000      0.00000000      0.00000000
 #      0.44276860     -0.00000000      0.28396338     -0.00000000      0.02380182
 #      0.49303352      0.70018316     -0.00000000      0.00000000      0.16114191
 #      0.50966987     -0.00000000     -0.00000000     -0.99314696      0.33513882
 #      0.66491116     -0.00000000     -0.64252098      0.00000000      0.18299828
 #      0.74291752      0.00000000      0.51393832      0.00000000      0.13081916
 #      0.74604777      0.89621414     -0.00000000     -0.00000000      0.39948361
 #      0.75917069      0.63465184     -0.00000000      0.00000000      0.20385401
 #      0.82076192      0.00000000      0.11163179      0.00000000      0.00681870
 #      0.82465720      0.00000000      0.00000000      1.21612905      0.81309543
 #      0.84970256     -0.00000000     -0.00000000      0.17496158      0.01734048
 #      0.85043026     -0.00000000      0.00000000     -0.39907741      0.09029459
 #      0.86392799     -0.00000000      0.00000000     -0.00000000      0.00000000
 #      0.87680042      0.41764603      0.00000000     -0.00000000      0.10195915
 #      0.90307953      0.00000000      0.00000000      0.00000000      0.00000000
 #      0.90773835      0.48641408      0.00000000     -0.00000000      0.14317978
 #      0.91469824      0.00000000     -0.37497291      0.00000000      0.08574057