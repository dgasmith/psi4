#
# @BEGIN LICENSE
#
# Psi4: an open-source quantum chemistry software package
#
# Copyright (c) 2007-2019 The Psi4 Developers.
#
# The copyrights for code used from other parties are included in
# the corresponding files.
#
# This file is part of Psi4.
#
# Psi4 is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, version 3.
#
# Psi4 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with Psi4; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# @END LICENSE
#

import re
import math

from psi4 import core
from psi4.driver import p4util
from psi4.driver.p4util.exceptions import ValidationError, MissingMethodError, ManagedMethodError, UpgradeHelper
from psi4.driver.procrouting import *


def negotiate_convergence_criterion(dermode, method, return_optstash=False):
    r"""
    This function will set local SCF and global energy convergence criterion
    to the defaults listed at:
    http://www.psicode.org/psi4manual/master/scf.html#convergence-and-
    algorithm-defaults. SCF will be converged more tightly if a post-SCF
    method is select (pscf_Ec, and pscf_Dc) else the looser (scf_Ec, and
    scf_Dc convergence criterion will be used).

    ptype -         Procedure type (energy, gradient, etc). Nearly always test on
                    procedures['energy'] since that's guaranteed to exist for a method.
    method_name -   Name of the method
    scf_Ec -        E convergence criterion for scf target method
    pscf_Ec -       E convergence criterion for scf of post-scf target method
    scf_Dc -        D convergence criterion for scf target method
    pscf_Dc -       D convergence criterion for scf of post-scf target method
    gen_Ec -        E convergence criterion for post-scf target method

    """

    scf_Ec, pscf_Ec, scf_Dc, pscf_Dc, gen_Ec = {(0, 0): [ 6,   8,   6,   8,   6],
                                                (1, 0): [ 8,  10,   8,  10,   8],
                                                (2, 0): [10,  11,  10,  11,  10],
                                                (1, 1): [ 8,  10,   8,  10,   8],
                                                (2, 1): [ 8,  10,   8,  10,   8],
                                                (2, 2): [ 8,  10,   8,  10,   8],
                                                'prop': [ 6,  10,   6,  10,   8]}[dermode]

    # Set method-dependent scf convergence criteria, check against energy routines
    # Set post-scf convergence criteria (global will cover all correlated modules)
    cc = {}
    if procedures['energy'][method] in [proc.run_scf, proc.run_tdscf_energy]:
        if not core.has_option_changed('SCF', 'E_CONVERGENCE'):
            cc['SCF__E_CONVERGENCE'] = math.pow(10, -scf_Ec)
        if not core.has_option_changed('SCF', 'D_CONVERGENCE'):
            cc['SCF__D_CONVERGENCE'] = math.pow(10, -scf_Dc)
    else:
        if not core.has_option_changed('SCF', 'E_CONVERGENCE'):
            cc['SCF__E_CONVERGENCE'] = math.pow(10, -pscf_Ec)
        if not core.has_option_changed('SCF', 'D_CONVERGENCE'):
            cc['SCF__D_CONVERGENCE'] = math.pow(10, -pscf_Dc)
        if not core.has_global_option_changed('E_CONVERGENCE'):
            cc['E_CONVERGENCE'] = math.pow(10, -gen_Ec)

    if return_optstash:
        optstash = p4util.OptionsState(
            ['SCF', 'E_CONVERGENCE'],
            ['SCF', 'D_CONVERGENCE'],
            ['E_CONVERGENCE'])
        p4util.set_options(cc)
        return optstash

    else:
        return cc


def upgrade_interventions(method):
    try:
        lowermethod = method.lower()
    except AttributeError as e:
        if method.__name__ == 'cbs':
            raise UpgradeHelper(method, repr(method.__name__), 1.4, ' Replace cbs or complete_basis_set function with cbs string.')
        elif method.__name__ in ['sherrill_gold_standard', 'allen_focal_point']:
            raise UpgradeHelper('argument ' + method.__name__, 'function ' + method.__name__, 1.4, ' Replace `energy(sherrill_gold_standard)` with `sherrill_gold_standard(energy)` or similar.')
        else:
            raise e

    return lowermethod


def parse_arbitrary_order(name):
    r"""Function to parse name string into a method family like CI or MRCC and specific
    level information like 4 for CISDTQ or MRCCSDTQ.

    """

    name = name.lower()
    mtdlvl_mobj = re.match(r"""\A(?P<method>[a-z]+)(?P<level>\d+)\Z""", name)

    # matches 'mrccsdt(q)'
    if name.startswith('mrcc'):

        # avoid undoing fn's good work when called twice
        if name == 'mrcc':
            return name, None

        # grabs 'sdt(q)'
        ccfullname = name[4:]

        # A negative order indicates perturbative method
        methods = {
            'sd'          : { 'method': 1, 'order':  2, 'fullname': 'CCSD'         },
            'sdt'         : { 'method': 1, 'order':  3, 'fullname': 'CCSDT'        },
            'sdtq'        : { 'method': 1, 'order':  4, 'fullname': 'CCSDTQ'       },
            'sdtqp'       : { 'method': 1, 'order':  5, 'fullname': 'CCSDTQP'      },
            'sdtqph'      : { 'method': 1, 'order':  6, 'fullname': 'CCSDTQPH'     },
            'sd(t)'       : { 'method': 3, 'order': -3, 'fullname': 'CCSD(T)'      },
            'sdt(q)'      : { 'method': 3, 'order': -4, 'fullname': 'CCSDT(Q)'     },
            'sdtq(p)'     : { 'method': 3, 'order': -5, 'fullname': 'CCSDTQ(P)'    },
            'sdtqp(h)'    : { 'method': 3, 'order': -6, 'fullname': 'CCSDTQP(H)'   },
            'sd(t)_l'     : { 'method': 4, 'order': -3, 'fullname': 'CCSD(T)_L'    },
            'sdt(q)_l'    : { 'method': 4, 'order': -4, 'fullname': 'CCSDT(Q)_L'   },
            'sdtq(p)_l'   : { 'method': 4, 'order': -5, 'fullname': 'CCSDTQ(P)_L'  },
            'sdtqp(h)_l'  : { 'method': 4, 'order': -6, 'fullname': 'CCSDTQP(H)_L' },
            'sdt-1a'      : { 'method': 5, 'order':  3, 'fullname': 'CCSDT-1a'     },
            'sdtq-1a'     : { 'method': 5, 'order':  4, 'fullname': 'CCSDTQ-1a'    },
            'sdtqp-1a'    : { 'method': 5, 'order':  5, 'fullname': 'CCSDTQP-1a'   },
            'sdtqph-1a'   : { 'method': 5, 'order':  6, 'fullname': 'CCSDTQPH-1a'  },
            'sdt-1b'      : { 'method': 6, 'order':  3, 'fullname': 'CCSDT-1b'     },
            'sdtq-1b'     : { 'method': 6, 'order':  4, 'fullname': 'CCSDTQ-1b'    },
            'sdtqp-1b'    : { 'method': 6, 'order':  5, 'fullname': 'CCSDTQP-1b'   },
            'sdtqph-1b'   : { 'method': 6, 'order':  6, 'fullname': 'CCSDTQPH-1b'  },
            '2'           : { 'method': 7, 'order':  2, 'fullname': 'CC2'          },
            '3'           : { 'method': 7, 'order':  3, 'fullname': 'CC3'          },
            '4'           : { 'method': 7, 'order':  4, 'fullname': 'CC4'          },
            '5'           : { 'method': 7, 'order':  5, 'fullname': 'CC5'          },
            '6'           : { 'method': 7, 'order':  6, 'fullname': 'CC6'          },
            'sdt-3'       : { 'method': 8, 'order':  3, 'fullname': 'CCSDT-3'      },
            'sdtq-3'      : { 'method': 8, 'order':  4, 'fullname': 'CCSDTQ-3'     },
            'sdtqp-3'     : { 'method': 8, 'order':  5, 'fullname': 'CCSDTQP-3'    },
            'sdtqph-3'    : { 'method': 8, 'order':  6, 'fullname': 'CCSDTQPH-3'   }
        }  # yapf: disable

        # looks for 'sdt(q)' in dictionary
        if ccfullname in methods:
            return 'mrcc', methods[ccfullname]
        else:
            raise ValidationError(f"""MRCC method '{name}' invalid.""")

    elif mtdlvl_mobj:
        namestump = mtdlvl_mobj.group('method')
        namelevel = int(mtdlvl_mobj.group('level'))

        if namestump in ['mp', 'zapt', 'ci']:
            # Let mp2, mp3, mp4 pass through to select functions
            if namestump == 'mp' and namelevel in [2, 3, 4]:
                return name, None
            # Otherwise return method and order
            else:
                return namestump, namelevel
        else:
            return name, None
    else:
        return name, None


def parse_cotton_irreps(irrep, point_group):
    """Return validated Cotton ordering index of `irrep` within `point_group`.

    Parameters
    ----------
    irrep : str or int
        Irreducible representation. Either label (case-insensitive) or 1-based index (int or str).
    point_group : str
        Molecular point group label (case-insensitive).

    Returns
    -------
    int
        1-based index for `irrep` within `point_group` in Cotton ordering.

    Raises
    ------
    ValidationError
        If `irrep` out-of-bounds or invalid or if `point_group` doesn't exist.

    """
    cotton = {
        'c1': ['a'],
        'ci': ['ag', 'au'],
        'c2': ['a', 'b'],
        'cs': ['ap', 'app'],
        'd2': ['a', 'b1', 'b2', 'b3'],
        'c2v': ['a1', 'a2', 'b1', 'b2'],
        'c2h': ['ag', 'bg', 'au', 'bu'],
        'd2h': ['ag', 'b1g', 'b2g', 'b3g', 'au', 'b1u', 'b2u', 'b3u'],
    }

    boll = cotton[point_group.lower()]

    if str(irrep).isdigit():
        irrep = int(irrep)
        if irrep > 0 and irrep <= len(boll):
            return irrep
    else:
        if irrep.lower() in boll:
            return boll.index(irrep.lower()) + 1

    raise ValidationError(f"""Irrep '{irrep}' not valid for point group '{point_group}'.""")


def negotiate_derivative_type(ptype, method, user_dertype, verbose=1, proc=None):
    r"""Find the best derivative level (0, 1, 2) and strategy (analytic, finite difference)
    for `method` to achieve `ptype` within constraints of `user_dertype`.

    Procedures
    ----------
    ptype : {'energy', 'gradient', 'hessian'}
        Type of calculation targeted by driver.
    method : str
        Quantum chemistry method targeted by driver. Should be correct case for procedures lookup.
    user_dertype : int or None
        User input on which derivative level should be employed to achieve `ptype`.
    verbose : int, optional
        Control amount of output printing.
    proc : dict, optional
        For testing only! Procedures table to look up `method`. Default is psi4.driver.procedures .

    Returns
    -------
    tuple : (int, int)
        "second" is highest accessible derivative level for `method` to achieve
        `ptype` "first" within constraints of `user_dertype`. When
        "first" == "second", analytic is the best strategy, otherwise finite
        difference of target "first" by means of "second".

    Raises
    ------
    ValidationError
        When input validation fails. When `user_dertype` exceeds `ptype`.
    MissingMethodError
        When `method` is unavailable at all. When `user_dertype` exceeds what available for `method`.

    """
    egh = ['energy', 'gradient', 'hessian']

    def alternative_methods_message(method_name, dertype):
        alt_method_name = p4util.text.find_approximate_string_matches(method_name, proc['energy'].keys(), 2)

        alternatives = ''
        if len(alt_method_name) > 0:
            alternatives = f""" Did you mean? {' '.join(alt_method_name)}"""

        return f"""Derivative method ({method_name}) and derivative level ({dertype}) are not available.{alternatives}"""

    # Validate input dertypes
    if ptype not in egh:
        raise ValidationError("_find_derivative_type: ptype must either be gradient or hessian.")

    if not (user_dertype is None or isinstance(user_dertype, int)):
        raise ValidationError(f"user_dertype ({user_dertype}) should only be None or int!")

    if proc is None:
        proc = procedures

    dertype = "(auto)"

    # Find the highest dertype program can provide for method, as encoded in procedures and managed methods
    #   Managed methods return finer grain "is available" info. For example, "is analytic ROHF DF HF gradient available?"
    #   from managed method, not just "is HF gradient available?" from procedures.
    if method in proc['hessian']:
        dertype = 2
        if proc['hessian'][method].__name__.startswith('select_'):
            try:
                proc['hessian'][method](method, probe=True)
            except ManagedMethodError:
                dertype = 1
                if proc['gradient'][method].__name__.startswith('select_'):
                    try:
                        proc['gradient'][method](method, probe=True)
                    except ManagedMethodError:
                        dertype = 0
                        if proc['energy'][method].__name__.startswith('select_'):
                            try:
                                proc['energy'][method](method, probe=True)
                            except ManagedMethodError:
                                raise MissingMethodError(alternative_methods_message(method, 'any'))

    elif method in proc['gradient']:
        dertype = 1
        if proc['gradient'][method].__name__.startswith('select_'):
            try:
                proc['gradient'][method](method, probe=True)
            except ManagedMethodError:
                dertype = 0
                if proc['energy'][method].__name__.startswith('select_'):
                    try:
                        proc['energy'][method](method, probe=True)
                    except ManagedMethodError:
                        raise MissingMethodError(alternative_methods_message(method, 'any'))

    elif method in proc['energy']:
        dertype = 0
        if proc['energy'][method].__name__.startswith('select_'):
            try:
                proc['energy'][method](method, probe=True)
            except ManagedMethodError:
                raise MissingMethodError(alternative_methods_message(method, 'any'))

    highest_der_program_can_provide = dertype

    # Negotiations. In particular:
    # * don't return higher derivative than targeted by driver
    # * don't return higher derivative than spec'd by user. that is, user can downgrade derivative
    # * alert user to conflict between driver and user_dertype

    if user_dertype is not None and user_dertype > egh.index(ptype):
        raise ValidationError(f'User dertype ({user_dertype}) excessive for target calculation ({ptype})')

    if dertype != "(auto)" and egh.index(ptype) < dertype:
        dertype = egh.index(ptype)

    if dertype != "(auto)" and user_dertype is not None:
        if user_dertype <= dertype:
            dertype = user_dertype
        else:
            raise MissingMethodError(alternative_methods_message(method, user_dertype))

    # hack section
    if core.get_global_option('PCM') and dertype != 0:
        core.print_out('\nPCM analytic gradients are not implemented yet, re-routing to finite differences.\n')
        dertype = 0

    if verbose > 1:
        print(
            f'Dertivative negotiations: target/driver={egh.index(ptype)}, best_available={highest_der_program_can_provide}, user_dertype={user_dertype}, FINAL={dertype}'
        )

    #if (core.get_global_option('INTEGRAL_PACKAGE') == 'ERD') and (dertype != 0):
    #    raise ValidationError('INTEGRAL_PACKAGE ERD does not play nicely with derivatives, so stopping.')

    # Summary validation (superfluous)
    if dertype == '(auto)' or method not in proc[['energy', 'gradient', 'hessian'][dertype]]:
        raise MissingMethodError(alternative_methods_message(method, dertype))

    if ptype == egh[dertype]:
        return (dertype, dertype)
    elif ptype == 'gradient' and egh[dertype] == 'energy':
        return (1, 0)
    elif ptype == 'hessian' and egh[dertype] == 'gradient':
        return (2, 1)
    elif ptype == 'hessian' and egh[dertype] == 'energy':
        return (2, 0)
