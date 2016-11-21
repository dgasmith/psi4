/*
 * @BEGIN LICENSE
 *
 * Psi4: an open-source quantum chemistry software package
 *
 * Copyright (c) 2007-2017 The Psi4 Developers.
 *
 * The copyrights for code used from other parties are included in
 * the corresponding files.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program; if not, write to the Free Software Foundation, Inc.,
 * 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
 *
 * @END LICENSE
 */

 #include "psi4/pragma.h"
 PRAGMA_WARNING_PUSH
 PRAGMA_WARNING_IGNORE_DEPRECATED_DECLARATIONS
 #include <memory>
 PRAGMA_WARNING_POP
#include "libxc/xc.h"
#include "psi4/psi4-dec.h"
#include "functional.h"
#include "LibXCfunctional.h"

namespace psi {

std::shared_ptr<Functional> Functional::build_base(const std::string& alias)
{
    Functional* fun;

    if (xc_functional_get_number(alias.c_str()) >= 0){
        fun = static_cast<Functional*>(new LibXCFunctional(alias, false));
    } else {
        throw PSIEXCEPTION("Functional::build_base: Unrecognized base Functional.");
    }

    return std::shared_ptr<Functional>(fun);
}

}
